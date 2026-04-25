from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import text
from datetime import datetime, timedelta
import threading
import time

from database.models import (
    db, Student, Lecturer, Session,
    AttendanceRecord, QRToken,
    Course, StudentCourse
)

from qr_engine.token_generator import generate_token, generate_qr

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'default_secret'

app.config['QR_EXPIRY_MINUTES'] = 5
app.config['TOKEN_INTERVAL'] = 30

db.init_app(app)

# ================= INIT DB =================
with app.app_context():
    db.create_all()

# =========================================================
# ================= AUTO QR BACKGROUND =====================
# =========================================================

def auto_generate_qr(session_id):
    with app.app_context():
        start_time = time.time()

        while time.time() - start_time < app.config['QR_EXPIRY_MINUTES'] * 60:
            token_str = generate_token()
            qr_file = generate_qr(token_str)

            token = QRToken(
                token=token_str,
                session_id=session_id,
                expires_at=datetime.utcnow() + timedelta(
                    seconds=app.config['TOKEN_INTERVAL']
                )
            )

            db.session.add(token)
            db.session.commit()

            print(f"[AUTO QR] New token: {token_str}")

            time.sleep(app.config['TOKEN_INTERVAL'])

# =========================================================
# ================= STUDENT =================
# =========================================================

@app.route('/api/student/login', methods=['POST'])
def student_login():
    data = request.get_json()
    nim = data.get('nim')

    if not nim:
        return jsonify({"status": "error", "message": "NIM is required"}), 400

    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404

    courses = db.session.query(Course).join(StudentCourse).filter(
        StudentCourse.student_nim == nim
    ).all()

    course_list = [
        {"course_id": c.course_id, "course_name": c.course_name}
        for c in courses
    ]

    return jsonify({
        "status": "success",
        "data": {
            **student.to_dict(),
            "courses": course_list
        }
    })


@app.route('/api/student/<nim>/profile', methods=['GET'])
def get_student_profile(nim):
    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error"}), 404

    return jsonify({"status": "success", "data": student.to_dict()})


@app.route('/api/student/<nim>/courses', methods=['GET'])
def get_student_courses(nim):
    courses = db.session.query(Course).join(StudentCourse).filter(
        StudentCourse.student_nim == nim
    ).all()

    return jsonify({
        "status": "success",
        "data": [c.to_dict() for c in courses]
    })


@app.route('/api/student/<nim>/history', methods=['GET'])
def get_student_history(nim):
    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error"}), 404

    history = [r.to_dict() for r in student.attendances]
    return jsonify({"status": "success", "data": history})


# =========================================================
# ================= LECTURER =================
# =========================================================

@app.route('/api/lecturer/login', methods=['POST'])
def lecturer_login():
    data = request.get_json()

    lecturer = Lecturer.query.filter_by(
        username=data.get('username')
    ).first()

    if lecturer and lecturer.password == data.get('password'):
        return jsonify({"status": "success", "data": lecturer.to_dict()})

    return jsonify({"status": "error", "message": "Invalid login"}), 401


# =========================================================
# ================= SESSION =================
# =========================================================

@app.route('/api/session/create', methods=['POST'])
def create_session():
    data = request.get_json()

    lecturer_id = data.get('lecturer_id')
    course_id = data.get('course_id')

    if not lecturer_id or not course_id:
        return jsonify({
            "status": "error",
            "message": "lecturer_id & course_id required"
        }), 400

    lecturer = Lecturer.query.get(lecturer_id)
    course = Course.query.get(course_id)

    if not lecturer or not course:
        return jsonify({"status": "error", "message": "Invalid data"}), 404

    expires_at = datetime.utcnow() + timedelta(
        minutes=app.config['QR_EXPIRY_MINUTES']
    )

    session = Session(
        lecturer_id=lecturer_id,
        course_id=course_id,
        expires_at=expires_at
    )

    db.session.add(session)
    db.session.commit()

    # 🔥 AUTO QR START (GANTI REFRESH MANUAL)
    threading.Thread(
        target=auto_generate_qr,
        args=(session.session_id,)
    ).start()

    return jsonify({
        "status": "success",
        "session_id": session.session_id,
        "course_id": course_id
    })


@app.route('/api/session/<int:session_id>/current-qr', methods=['GET'])
def get_current_qr(session_id):
    token = QRToken.query.filter_by(session_id=session_id)\
        .order_by(QRToken.expires_at.desc())\
        .first()

    if not token:
        return jsonify({"status": "error", "message": "No QR"}), 404

    return jsonify({
        "status": "success",
        "token": token.token
    })


# =========================================================
# ================= ATTENDANCE =================
# =========================================================

@app.route('/api/attendance/scan', methods=['POST'])
def scan_attendance():
    data = request.get_json()

    nim = data.get('nim')
    token_str = data.get('token_qr')

    if not nim or not token_str:
        return jsonify({"status": "error"}), 400

    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error"}), 404

    qr_token = QRToken.query.filter_by(token=token_str).first()

    if not qr_token or not qr_token.is_valid():
        return jsonify({
            "status": "error",
            "message": "Invalid / expired QR"
        }), 400

    session = Session.query.get(qr_token.session_id)

    if not session or not session.is_active():
        return jsonify({
            "status": "error",
            "message": "Session expired"
        }), 400

    # VALIDASI COURSE
    student_course = StudentCourse.query.filter_by(
        student_nim=nim,
        course_id=session.course_id
    ).first()

    if not student_course:
        return jsonify({
            "status": "error",
            "message": "Not enrolled"
        }), 403

    # CEK DOUBLE ABSEN
    existing = AttendanceRecord.query.filter_by(
        nim=nim,
        session_id=session.session_id
    ).first()

    if existing:
        return jsonify({
            "status": "error",
            "message": "Already attended"
        }), 400

    attendance = AttendanceRecord(
        nim=nim,
        session_id=session.session_id,
        token=token_str,
        timestamp=datetime.utcnow()
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Attendance recorded"
    })


# =========================================================
# ================= LIVE DATA =================
# =========================================================

@app.route('/api/attendance/live/<int:session_id>', methods=['GET'])
def live_attendance(session_id):
    records = db.session.query(AttendanceRecord, Student)\
        .join(Student, Student.nim == AttendanceRecord.nim)\
        .filter(AttendanceRecord.session_id == session_id)\
        .all()

    result = []
    for record, student in records:
        result.append({
            "name": student.nama,
            "nim": student.nim,
            "time": record.timestamp,
            "token": record.token
        })

    return jsonify({"status": "success", "data": result})


@app.route('/api/attendance/count/<int:session_id>', methods=['GET'])
def count_attendance(session_id):
    count = AttendanceRecord.query.filter_by(session_id=session_id).count()
    return jsonify({"status": "success", "total": count})


@app.route('/api/attendance/notyet/<int:session_id>', methods=['GET'])
def not_attended(session_id):
    attended = db.session.query(AttendanceRecord.nim)\
        .filter_by(session_id=session_id)

    students = Student.query.filter(~Student.nim.in_(attended)).all()

    return jsonify({
        "status": "success",
        "data": [s.to_dict() for s in students]
    })


# =========================================================
# ================= ADMIN =================
# =========================================================

@app.route('/api/admin/add-student', methods=['POST'])
def add_student():
    data = request.get_json()

    student = Student(
        nim=data.get('nim'),
        nama=data.get('nama'),
        major=data.get('major'),
        faculty=data.get('faculty'),
        university=data.get('university')
    )

    db.session.add(student)
    db.session.commit()

    return jsonify({"status": "success"})


@app.route('/api/admin/add-course', methods=['POST'])
def add_course():
    data = request.get_json()

    course = Course(
        course_name=data.get('course_name'),
        lecturer_id=data.get('lecturer_id')
    )

    db.session.add(course)
    db.session.commit()

    return jsonify({"status": "success"})


@app.route('/api/admin/assign-course', methods=['POST'])
def assign_course():
    data = request.get_json()

    rel = StudentCourse(
        student_nim=data.get('nim'),
        course_id=data.get('course_id')
    )

    db.session.add(rel)
    db.session.commit()

    return jsonify({"status": "success"})


# =========================================================
# ================= UTIL =================
# =========================================================

@app.route('/api/init-db')
def init_db():
    db.drop_all()
    db.create_all()
    return jsonify({"status": "success"})


@app.route('/api/seed-data')
def seed_data():
    try:
        if not Student.query.first():
            s1 = Student(nim="23670708027", nama="Mutia Apriani", major="BTBS", faculty="Fen", university="Bartin")
            s2 = Student(nim="22670708061", nama="Thoriq", major="BTBS", faculty="Fen", university="Bartin")

            db.session.add_all([s1, s2])

        if not Lecturer.query.first():
            l1 = Lecturer(nama="Ramazan Yilmaz", username="admin", password="admin")
            db.session.add(l1)
            db.session.commit()

            c1 = Course(course_name="Gorsel Programlama", lecturer_id=l1.lecturer_id)

            db.session.add(c1)
            db.session.commit()

            sc1 = StudentCourse(student_nim="23670708027", course_id=c1.course_id)
            db.session.add(sc1)

        db.session.commit()
        return jsonify({"status": "success"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})


@app.route('/')
def index():
    return jsonify({"status": "connected"})


# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)