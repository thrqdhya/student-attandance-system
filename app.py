from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import uuid
import hashlib
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///qr_attendance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret')

db = SQLAlchemy(app)

# Models (Keep existing ones)
class Student(db.Model):
    __tablename__ = 'students'
    nim = db.Column(db.String(20), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), default='password123') # Default password
    attendances = db.relationship('AttendanceRecord', backref='student', lazy=True)

    def to_dict(self):
        return {"nim": self.nim, "nama": self.nama}

class Lecturer(db.Model):
    __tablename__ = 'lecturers'
    lecturer_id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), default='admin123') # Default password
    sessions = db.relationship('Session', backref='lecturer', lazy=True)

    def to_dict(self):
        return {
            "lecturer_id": self.lecturer_id, 
            "nama": self.nama,
            "username": self.username
        }

class Session(db.Model):
    __tablename__ = 'sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False) # Expiry for QR token
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.lecturer_id'), nullable=False)
    token_qr = db.Column(db.String(255), unique=True, nullable=False)
    attendances = db.relationship('AttendanceRecord', backref='session', lazy=True)

    def to_dict(self):
        is_expired = datetime.utcnow() > self.expires_at
        return {
            "session_id": self.session_id,
            "tanggal": self.tanggal.strftime('%Y-%m-%d %H:%M:%S'),
            "expires_at": self.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            "is_expired": is_expired,
            "lecturer_id": self.lecturer_id,
            "token_qr": self.token_qr,
            "total_attendance": len(self.attendances)
        }

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    record_id = db.Column(db.Integer, primary_key=True)
    nim = db.Column(db.String(20), db.ForeignKey('students.nim'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'), nullable=False)
    waktu_absen = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "nim": self.nim,
            "student_name": self.student.nama,
            "session_id": self.session_id,
            "waktu_absen": self.waktu_absen.strftime('%Y-%m-%d %H:%M:%S')
        }

# --- Helper Functions (Core Logic) ---

def validate_nim(nim):
    """Cek apakah NIM ada di database (untuk login student)"""
    return Student.query.filter_by(nim=nim).first()

def generate_secure_token(lecturer_id):
    """Generate QR token unik menggunakan hashing (SESSION + waktu + secret)"""
    # Prototype logic: hash("SESSION_ID + lecturer_id + waktu + secret")
    timestamp = str(time.time())
    secret = app.config['SECRET_KEY']
    raw_data = f"SESSION_{lecturer_id}_{timestamp}_{secret}"
    return hashlib.sha256(raw_data.encode()).hexdigest()

# 1. Feature: Student Login
@app.route('/api/student/login', methods=['POST'])
def student_login():
    data = request.get_json()
    nim = data.get('nim')
    # Client request says "validate_nim() used when login student"
    
    if not nim:
        return jsonify({"status": "error", "message": "NIM is required"}), 400

    student = validate_nim(nim)
    if student:
        return jsonify({
            "status": "success",
            "message": "Student login successful",
            "data": student.to_dict()
        })
    else:
        return jsonify({"status": "error", "message": "NIM not found"}), 404

# 2. Feature: Lecturer Login
@app.route('/api/lecturer/login', methods=['POST'])
def lecturer_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required"}), 400

    lecturer = Lecturer.query.filter_by(username=username).first()
    if lecturer and lecturer.password == password:
        return jsonify({
            "status": "success",
            "message": "Lecturer login successful",
            "data": lecturer.to_dict()
        })
    else:
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

# 3. Feature: Student Profile & History
@app.route('/api/student/<nim>/profile', methods=['GET'])
def get_student_profile(nim):
    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404
    
    return jsonify({
        "status": "success",
        "data": student.to_dict()
    })

@app.route('/api/student/<nim>/history', methods=['GET'])
def get_student_history(nim):
    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404
    
    history = [record.to_dict() for record in student.attendances]
    return jsonify({
        "status": "success",
        "data": history
    })

# 4. Feature: Lecturer Sessions & Attendance Reports
@app.route('/api/lecturer/<int:lecturer_id>/sessions', methods=['GET'])
def get_lecturer_sessions(lecturer_id):
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return jsonify({"status": "error", "message": "Lecturer not found"}), 404
    
    sessions = [session.to_dict() for session in lecturer.sessions]
    return jsonify({
        "status": "success",
        "data": sessions
    })

@app.route('/api/session/<int:session_id>/attendance', methods=['GET'])
def get_session_attendance(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    attendance_list = [record.to_dict() for record in session.attendances]
    return jsonify({
        "status": "success",
        "data": {
            "session_info": session.to_dict(),
            "attendance_list": attendance_list
        }
    })

# --- Endpoint: Create Session ---
@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Fungsi create_session() - Bikin sesi baru + generate QR token"""
    data = request.get_json()
    lecturer_id = data.get('lecturer_id')

    if not lecturer_id:
        return jsonify({"status": "error", "message": "Lecturer ID is required"}), 400

    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return jsonify({"status": "error", "message": "Lecturer not found"}), 404

    # Use secure hashing instead of UUID
    token_qr = generate_secure_token(lecturer_id)
    
    # Set expiry time (e.g., 60 minutes from now)
    expiry_minutes = int(os.getenv('QR_EXPIRY_MINUTES', 60))
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    
    new_session = Session(
        lecturer_id=lecturer_id, 
        token_qr=token_qr,
        expires_at=expires_at
    )
    
    try:
        db.session.add(new_session)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Secure Session created",
            "data": new_session.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Endpoint: Save Attendance ---
@app.route('/api/attendance/scan', methods=['POST'])
def save_attendance():
    """Fungsi save_attendance() - Simpan data absensi saat scan QR"""
    data = request.get_json()
    nim = data.get('nim')
    token_qr = data.get('token_qr')

    if not nim or not token_qr:
        return jsonify({"status": "error", "message": "NIM and token_qr are required"}), 400

    student = Student.query.get(nim)
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404

    session = Session.query.filter_by(token_qr=token_qr).first()
    if not session:
        return jsonify({"status": "error", "message": "Invalid QR Token"}), 404

    # Security check: check if token is expired
    if datetime.utcnow() > session.expires_at:
        return jsonify({"status": "error", "message": "QR Token has expired"}), 403

    # Check if already attended
    existing_record = AttendanceRecord.query.filter_by(nim=nim, session_id=session.session_id).first()
    if existing_record:
        return jsonify({"status": "error", "message": "Attendance already recorded for this session"}), 400

    new_attendance = AttendanceRecord(nim=nim, session_id=session.session_id)
    
    try:
        db.session.add(new_attendance)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Attendance recorded successfully",
            "data": new_attendance.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# Seed Data Endpoint for Testing
@app.route('/api/seed-data')
def seed_data():
    try:
        # Check if data already exists to avoid duplicates
        if not Student.query.first():
            s1 = Student(nim="12345", nama="Budi Santoso", password="password123")
            s2 = Student(nim="67890", nama="Ani Wijaya", password="password123")
            db.session.add_all([s1, s2])
        
        if not Lecturer.query.first():
            l1 = Lecturer(nama="Dr. Irfan", username="irfan", password="admin123")
            l2 = Lecturer(nama="Prof. Maya", username="maya", password="admin123")
            db.session.add_all([l1, l2])
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Sample data seeded!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    try:
        db.session.execute(text('SELECT 1'))
        db_status = "Connected"
    except Exception as e:
        db_status = f"Disconnected: {str(e)}"

    return jsonify({
        "status": "success",
        "message": "Backend Flask API is running!",
        "database": db_status
    })

@app.route('/api/init-db')
def init_db():
    try:
        # Drop all tables first to ensure new schema is applied
        db.drop_all()
        db.create_all()
        return jsonify({
            "status": "success",
            "message": "Database tables reset and created successfully!"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to create tables: {str(e)}"
        }), 500

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "up",
        "environment": os.getenv('FLASK_ENV', 'development')
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
