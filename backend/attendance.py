from database.models import Student, Session, AttendanceRecord, db
from datetime import datetime
from qr_engine.token_generator import validate_token


def save_attendance_logic(nim, token_qr):
    """
    Proses absensi mahasiswa
    """

    # 🔹 1. Cek student
    student = Student.query.get(nim)
    if not student:
        return None, "Student not found"

    # 🔹 2. Validasi token (dynamic 30 detik)
    if not validate_token(token_qr):
        return None, "Invalid or expired QR Token"

    # 🔹 3. Cek session berdasarkan token
    session = Session.query.filter_by(token_qr=token_qr).first()
    if not session:
        return None, "Session not found"

    # 🔹 4. Cek apakah session masih aktif (5 menit)
    if datetime.utcnow() > session.expires_at:
        return None, "Session has expired"

    # 🔹 5. Cek apakah sudah absen
    existing = AttendanceRecord.query.filter_by(
        nim=nim,
        session_id=session.session_id
    ).first()

    if existing:
        return None, "Attendance already recorded"

    # 🔹 6. Simpan attendance (ubah ke English)
    new_record = AttendanceRecord(
        nim=nim,
        session_id=session.session_id,
        status="PRESENT",  # 🔥 ubah dari HADIR → PRESENT
        timestamp=datetime.utcnow()
    )

    db.session.add(new_record)
    db.session.commit()

    return new_record, None