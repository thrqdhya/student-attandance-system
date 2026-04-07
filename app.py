from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import text
from datetime import datetime, timedelta

# 🔥 TAMBAH QRToken
from database.models import db, Student, Lecturer, Session, AttendanceRecord, QRToken

from backend.student import validate_nim
from qr_engine.token_generator import generate_token, generate_qr

app = Flask(__name__)
CORS(app)

# 🔥 CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'default_secret'

app.config['QR_EXPIRY_MINUTES'] = 5
app.config['TOKEN_INTERVAL'] = 30

db.init_app(app)

# ---------------- INIT DB ----------------
with app.app_context():
    db.create_all()

# ---------------- STUDENT ----------------

@app.route('/api/student/login', methods=['POST'])
def student_login():
    data = request.get_json()
    nim = data.get('nim')

    if not nim:
        return jsonify({"status": "error", "message": "NIM is required"}), 400

    student = validate_nim(nim)
    if student:
        return jsonify({"status": "success", "data": student.to_dict()})
    else:
        return jsonify({"status": "error", "message": "Student not found"}), 404


@app.route('/api/student/<nim>/profile', methods=['GET'])
def get_student_profile(nim):
    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404

    return jsonify({"status": "success", "data": student.to_dict()})


@app.route('/api/student/<nim>/history', methods=['GET'])
def get_student_history(nim):
    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404

    history = [r.to_dict() for r in student.attendances]
    return jsonify({"status": "success", "data": history})


# ---------------- LECTURER ----------------

@app.route('/api/lecturer/login', methods=['POST'])
def lecturer_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    lecturer = Lecturer.query.filter_by(username=username).first()

    if lecturer and lecturer.password == password:
        return jsonify({"status": "success", "data": lecturer.to_dict()})
    else:
        return jsonify({"status": "error", "message": "Invalid login"}), 401


@app.route('/api/lecturer/<int:lecturer_id>/sessions', methods=['GET'])
def get_sessions(lecturer_id):
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return jsonify({"status": "error", "message": "Lecturer not found"}), 404

    sessions = [s.to_dict() for s in lecturer.sessions]
    return jsonify({"status": "success", "data": sessions})


# ---------------- SESSION ----------------

# 🔥 CREATE SESSION + TOKEN PERTAMA
@app.route('/api/session/create', methods=['POST'])
def create_session():
    data = request.get_json()
    lecturer_id = data.get('lecturer_id')

    if not lecturer_id:
        return jsonify({"status": "error", "message": "lecturer_id required"}), 400

    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return jsonify({"status": "error", "message": "Lecturer not found"}), 404

    expires_at = datetime.utcnow() + timedelta(minutes=app.config['QR_EXPIRY_MINUTES'])

    session = Session(
        lecturer_id=lecturer_id,
        expires_at=expires_at
    )

    db.session.add(session)
    db.session.commit()

    # 🔥 TOKEN PERTAMA
    token_str = generate_token()
    qr_file = generate_qr(token_str)

    token = QRToken(
        token=token_str,
        session_id=session.session_id,
        expires_at=datetime.utcnow() + timedelta(seconds=app.config['TOKEN_INTERVAL'])
    )

    db.session.add(token)
    db.session.commit()

    return jsonify({
        "status": "success",
        "session_id": session.session_id,
        "qr_file": qr_file,
        "message": "Session started"
    })


# 🔥 REFRESH QR (DINAMIS)
@app.route('/api/session/<int:session_id>/refresh-qr', methods=['GET'])
def refresh_qr(session_id):
    session = Session.query.get(session_id)

    if not session or not session.is_active():
        return jsonify({"status": "error", "message": "Session expired"}), 400

    token_str = generate_token()
    qr_file = generate_qr(token_str)

    new_token = QRToken(
        token=token_str,
        session_id=session_id,
        expires_at=datetime.utcnow() + timedelta(seconds=app.config['TOKEN_INTERVAL'])
    )

    db.session.add(new_token)
    db.session.commit()

    return jsonify({
        "status": "success",
        "token": token_str,
        "qr_file": qr_file
    })


@app.route('/api/session/<int:session_id>/attendance', methods=['GET'])
def get_session_attendance(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    attendance = [r.to_dict() for r in session.attendances]

    return jsonify({
        "status": "success",
        "data": {
            "session_info": session.to_dict(),
            "attendance_list": attendance
        }
    })


# ---------------- ATTENDANCE ----------------

@app.route('/api/attendance/scan', methods=['POST'])
def scan_attendance():
    data = request.get_json()
    nim = data.get('nim')
    token_str = data.get('token_qr')

    if not nim or not token_str:
        return jsonify({
            "status": "error",
            "message": "nim and token_qr required"
        }), 400

    # 🔥 1. STUDENT
    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404

    # 🔥 2. TOKEN VALIDASI (ANTI SHARE)
    qr_token = QRToken.query.filter_by(token=token_str).first()

    if not qr_token:
        return jsonify({"status": "error", "message": "Invalid QR"}), 400

    if not qr_token.is_valid():
        return jsonify({"status": "error", "message": "QR expired"}), 400

    # 🔥 3. SESSION VALID
    session = Session.query.get(qr_token.session_id)

    if not session or not session.is_active():
        return jsonify({"status": "error", "message": "Session expired"}), 400

    # 🔥 4. CEK SUDAH ABSEN
    existing = AttendanceRecord.query.filter_by(
        nim=nim,
        session_id=session.session_id
    ).first()

    if existing:
        return jsonify({
            "status": "error",
            "message": "Already attended"
        }), 400

    # 🔥 5. SAVE
    attendance = AttendanceRecord(
        nim=nim,
        session_id=session.session_id,
        status="PRESENT",
        timestamp=datetime.utcnow()
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        "status": "success",
        "data": attendance.to_dict(),
        "message": "Attendance recorded"
    })


# ---------------- UTIL ----------------

@app.route('/api/init-db')
def init_db():
    db.drop_all()
    db.create_all()
    return jsonify({"status": "success"})


@app.route('/')
def index():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "connected"})
    except:
        return jsonify({"status": "error"})


@app.route('/api/seed-data')
def seed_data():
    try:
        if not Student.query.first():
            db.session.add_all([
                Student(nim="12345", nama="Budi"),
                Student(nim="67890", nama="Ani")
            ])

        if not Lecturer.query.first():
            db.session.add_all([
                Lecturer(nama="Dr. A", username="admin", password="admin")
            ])

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})


@app.route('/test')
def test():
    return "OK"


# 🔥 INI HARUS PALING BAWAH
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)