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
            print("📷 scan results:", token)
            return token
        else:
            print("❌ The QR code cannot be scanned")
            return None

    except Exception as e:
        print("❌ Error while scanning the QR code:", e)
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
        print(f"🎓 The student  {student_id} successfully signed in")
        return True
    else:
        print(f"🚫 The student  {student_id} failed to sign in")
        return False