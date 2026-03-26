from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    nim = db.Column(db.String(20), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), default='password123')
    attendances = db.relationship('AttendanceRecord', backref='student', lazy=True)

    def to_dict(self):
        return {"nim": self.nim, "nama": self.nama}


class Lecturer(db.Model):
    __tablename__ = 'lecturers'
    lecturer_id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), default='admin123')
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
    expires_at = db.Column(db.DateTime, nullable=False)
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