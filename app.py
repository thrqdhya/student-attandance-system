from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import text

from database.models import db, Student, Lecturer, Session, AttendanceRecord
from backend.student import validate_nim
from backend.lecturer import create_session_logic
from backend.attendance import save_attendance_logic

app = Flask(__name__)
CORS(app)

# CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'default_secret'
app.config['QR_EXPIRY_MINUTES'] = 60

db.init_app(app)

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
        return jsonify({"status": "error", "message": "NIM not found"}), 404


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
        return jsonify({"status": "error"}), 404

    sessions = [s.to_dict() for s in lecturer.sessions]
    return jsonify({"status": "success", "data": sessions})


@app.route('/api/session/create', methods=['POST'])
def create_session():
    data = request.get_json()
    lecturer_id = data.get('lecturer_id')

    session, error = create_session_logic(lecturer_id)

    if error:
        return jsonify({"status": "error", "message": error}), 400

    return jsonify({"status": "success", "data": session.to_dict()})


@app.route('/api/session/<int:session_id>/attendance', methods=['GET'])
def get_session_attendance(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"status": "error"}), 404

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
    token = data.get('token_qr')

    record, error = save_attendance_logic(nim, token)

    if error:
        return jsonify({"status": "error", "message": error}), 400

    return jsonify({"status": "success", "data": record.to_dict()})

# ---------------- UTIL ----------------

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


if __name__ == '__main__':
    app.run(debug=True, port=5001)