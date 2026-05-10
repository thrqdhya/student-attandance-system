from database.models import Student, AttendanceRecord, Session

def validate_nim(nim):
    return Student.query.filter_by(nim=nim).first()

def get_student_stats_logic(nim):
    # Menghitung berapa kali mahasiswa ini hadir
    total_hadir = AttendanceRecord.query.filter_by(nim=nim).count()
    
    # Menghitung total seluruh sesi absen yang pernah dibuka
    total_sesi = Session.query.count()
    
    # Menghitung persentase
    persentase = (total_hadir / total_sesi * 100) if total_sesi > 0 else 0
    
    return {
        "total_hadir": total_hadir,
        "total_pertemuan": total_sesi,
        "persentase": f"{persentase:.1f}%",
        "status_warning": True if persentase < 75 else False
    }