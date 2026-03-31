import hashlib
import time
import qrcode
import os

SECRET_KEY = "super_secret_key"
QR_FOLDER = "qr_codes"

SESSION_DURATION = 300  # 5 menit (300 detik)
INTERVAL = 30  # update tiap 30 detik

# Pastikan folder ada
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)


def generate_token():
    current_time = int(time.time() / INTERVAL)
    raw = str(current_time) + SECRET_KEY
    return hashlib.sha256(raw.encode()).hexdigest()


def validate_token(token):
    return token == generate_token()


def generate_qr(token):
    filename = f"{QR_FOLDER}/qr_{token[:8]}.png"
    img = qrcode.make(token)
    img.save(filename)
    print(f"✅ QR code created: {filename}")
    return filename


def start_qr_session():
    """
    QR aktif selama 5 menit
    dan update tiap 30 detik
    """
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time

        if elapsed > SESSION_DURATION:
            print("⛔ Time's up! The QR code is no longer valid.")
            break

        token = generate_token()
        generate_qr(token)

        print(f"🟢 active tokens: {token}")
        print(f"⏳ remaining time: {int(SESSION_DURATION - elapsed)} detik\n")

        time.sleep(INTERVAL)