from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# 🔹 STUDENT
class Student(db.Model):
    __tablename__ = 'students'

    nim = db.Column(db.String(20), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

    # 🔥 TAMBAHAN DATA
    major = db.Column(db.String(100))
    faculty = db.Column(db.String(100))
    university = db.Column(db.String(100))

    password = db.Column(db.String(100), default='password123')

    device_id = db.Column(db.String(100), nullable=True)

    attendances = db.relationship('AttendanceRecord', backref='student', lazy=True)
    courses = db.relationship('StudentCourse', backref='student', lazy=True)

    def to_dict(self):
        return {
            "nim": self.nim,
            "nama": self.nama,
            "major": self.major,
            "faculty": self.faculty,
            "university": self.university
        }


# 🔹 LECTURER (ÖĞRETMEN)
class Lecturer(db.Model):
    __tablename__ = 'lecturers'

    lecturer_id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), default='admin123')

    sessions = db.relationship('Session', backref='lecturer', lazy=True)
    courses = db.relationship('Course', backref='lecturer', lazy=True)

    def to_dict(self):
        return {
            "lecturer_id": self.lecturer_id,
            "nama": self.nama,
            "username": self.username
        }


# 🔥 🔹 COURSE (DERS)
class Course(db.Model):
    __tablename__ = 'courses'

    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)

    lecturer_id = db.Column(
        db.Integer,
        db.ForeignKey('lecturers.lecturer_id'),
        nullable=False
    )

    students = db.relationship('StudentCourse', backref='course', lazy=True)

    def to_dict(self):
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "lecturer_id": self.lecturer_id
        }


# 🔥 🔹 RELASI STUDENT - COURSE
class StudentCourse(db.Model):
    __tablename__ = 'student_courses'

    id = db.Column(db.Integer, primary_key=True)

    student_nim = db.Column(
        db.String(20),
        db.ForeignKey('students.nim'),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.course_id'),
        nullable=False
    )


# 🔹 SESSION
class Session(db.Model):
    __tablename__ = 'sessions'

    session_id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)

    expires_at = db.Column(db.DateTime, nullable=False)

    lecturer_id = db.Column(
        db.Integer,
        db.ForeignKey('lecturers.lecturer_id'),
        nullable=False
    )

    # 🔥 TAMBAHAN: session untuk course tertentu
    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.course_id'),
        nullable=True
    )

    tokens = db.relationship('QRToken', backref='session', lazy=True)
    attendances = db.relationship('AttendanceRecord', backref='session', lazy=True)

    def is_active(self):
        return datetime.utcnow() <= self.expires_at

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "tanggal": self.tanggal.strftime('%Y-%m-%d %H:%M:%S'),
            "expires_at": self.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            "is_active": self.is_active(),
            "lecturer_id": self.lecturer_id,
            "course_id": self.course_id,
            "total_attendance": len(self.attendances)
        }


# 🔥 🔹 QR TOKEN
class QRToken(db.Model):
    __tablename__ = 'qr_tokens'

    token_id = db.Column(db.Integer, primary_key=True)

    token = db.Column(db.String(255), unique=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    session_id = db.Column(
        db.Integer,
        db.ForeignKey('sessions.session_id'),
        nullable=False
    )

    def is_valid(self):
        return datetime.utcnow() <= self.expires_at

    def to_dict(self):
        return {
            "token": self.token,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "expires_at": self.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            "session_id": self.session_id
        }


# 🔹 ATTENDANCE
class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    record_id = db.Column(db.Integer, primary_key=True)

    nim = db.Column(
        db.String(20),
        db.ForeignKey('students.nim'),
        nullable=False
    )

    session_id = db.Column(
        db.Integer,
        db.ForeignKey('sessions.session_id'),
        nullable=False
    )

    status = db.Column(db.String(20), default="PRESENT")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('nim', 'session_id', name='unique_attendance'),
    )

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "nim": self.nim,
            "student_name": self.student.nama,
            "session_id": self.session_id,
            "status": self.status,
            "timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }