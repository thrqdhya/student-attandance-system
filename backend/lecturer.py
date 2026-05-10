import hashlib
import time
import os
import pandas as pd
from flask import current_app
from database.models import Session, Lecturer, AttendanceRecord, StudentCourse, Student, db
from datetime import datetime, timedelta

def generate_secure_token(lecturer_id):
    timestamp = str(time.time())
    secret = current_app.config['SECRET_KEY']
    raw_data = f"SESSION_{lecturer_id}_{timestamp}_{secret}"
    return hashlib.sha256(raw_data.encode()).hexdigest()


def create_session_logic(lecturer_id):
    lecturer = Lecturer.query.get(lecturer_id)
    if not lecturer:
        return None, "Lecturer not found"

    token_qr = generate_secure_token(lecturer_id)

    expiry_minutes = current_app.config.get('QR_EXPIRY_MINUTES', 5)
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

    new_session = Session(
        lecturer_id=lecturer_id,
        token_qr=token_qr,
        expires_at=expires_at
    )

    db.session.add(new_session)
    db.session.commit()

    return new_session, None

# =========================================================
# 🔥 LOGIKA STATISTIK DOSEN
# =========================================================

def get_lecturer_stats_logic(session_id):
    """
    Menghitung berapa mahasiswa yang sudah absen vs total seharusnya
    """
    session = Session.query.get(session_id)
    if not session:
        return None, "Session not found"

    hadir_count = AttendanceRecord.query.filter_by(session_id=session_id).count()
    total_mahasiswa = StudentCourse.query.filter_by(course_id=session.course_id).count()
    belum_hadir = total_mahasiswa - hadir_count

    return {
        "session_id": session_id,
        "course_id": session.course_id,
        "statistik": {
            "hadir": hadir_count,
            "belum_hadir": belum_hadir if belum_hadir > 0 else 0,
            "total_mahasiswa": total_mahasiswa,
            "persentase_kehadiran": f"{(hadir_count / total_mahasiswa * 100) if total_mahasiswa > 0 else 0:.1f}%"
        }
    }, None

# =========================================================
# 📊 FITUR AUTO REPORT EXCEL (BARU)
# =========================================================

def export_attendance_to_excel(session_id):
    """
    Mengambil data absensi dan mengubahnya menjadi file Excel (.xlsx)
    """
    # 1. Ambil data gabungan antara AttendanceRecord dan Student
    # Kita butuh: NIM, Nama, Status, dan Waktu Absen
    records = db.session.query(
        AttendanceRecord.timestamp,
        Student.nim,
        Student.nama,
        AttendanceRecord.status
    ).join(Student, AttendanceRecord.nim == Student.nim)\
     .filter(AttendanceRecord.session_id == session_id).all()

    if not records:
        return None, "Tidak ada data absensi untuk sesi ini."

    # 2. Susun data ke dalam list untuk diolah oleh Pandas
    data_list = []
    for rec in records:
        data_list.append({
            "NIM": rec.nim,
            "Nama Mahasiswa": rec.nama,
            "Waktu Scan": rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Status": rec.status
        })

    # 3. Gunakan Pandas untuk membuat tabel (DataFrame)
    df = pd.DataFrame(data_list)

    # 4. Tentukan lokasi penyimpanan file (di dalam folder instance)
    filename = f"Laporan_Absensi_Sesi_{session_id}.xlsx"
    
    # Pastikan folder instance ada agar tidak error
    if not os.path.exists("instance"):
        os.makedirs("instance")
        
    filepath = os.path.join("instance", filename)

    # 5. Simpan ke file Excel
    df.to_excel(filepath, index=False)

    return filepath, None