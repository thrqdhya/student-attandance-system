from database.models import Student, Session, AttendanceRecord, db
from datetime import datetime

def save_attendance_logic(nim, token_qr):
    student = Student.query.get(nim)
    if not student:
        return None, "Student not found"

    session = Session.query.filter_by(token_qr=token_qr).first()
    if not session:
        return None, "Invalid QR Token"

    if datetime.utcnow() > session.expires_at:
        return None, "QR Token has expired"

    existing = AttendanceRecord.query.filter_by(
        nim=nim, session_id=session.session_id
    ).first()

    if existing:
        return None, "Attendance already recorded"

    new_record = AttendanceRecord(nim=nim, session_id=session.session_id)

    db.session.add(new_record)
    db.session.commit()

    return new_record, None