from pyzbar.pyzbar import decode
from PIL import Image
from qr_engine.token_generator import validate_token


def scan_qr(qr_file):
    """
    Scan QR dari file dan ambil token
    """
    try:
        img = Image.open(qr_file)
        result = decode(img)

        if result:
            token = result[0].data.decode()
            print("📷 Hasil scan:", token)
            return token
        else:
            print("❌ QR tidak terbaca")
            return None

    except Exception as e:
        print("❌ Error saat scan QR:", e)
        return None


def scan_and_validate(qr_file):
    """
    Scan + validasi token
    """
    token = scan_qr(qr_file)

    if token is None:
        return False, None

    if validate_token(token):
        print("✅ TOKEN VALID")
        return True, token
    else:
        print("⛔ TOKEN EXPIRED / INVALID")
        return False, token


def scan_for_attendance(qr_file, student_id):
    """
    Full flow untuk absensi:
    scan → validasi → return hasil
    """
    is_valid, token = scan_and_validate(qr_file)

    if is_valid:
        print(f"🎓 Mahasiswa {student_id} berhasil absen")
        return True
    else:
        print(f"🚫 Mahasiswa {student_id} gagal absen")
        return False