import hashlib
import time
import qrcode
import os
from datetime import datetime

# 🔐 SECRET (harus sama di semua sistem)
SECRET_KEY = "super_secret_key"

QR_FOLDER = "qr_codes"

SESSION_DURATION = 300  # 5 menit
INTERVAL = 30           # 30 detik

# 📁 Pastikan folder ada
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)


# 🔥 GENERATE TOKEN (TIME-BASED + FORMAT JELAS)
def generate_token():
    """
    Format:
    ATTEND-YYYYMMDD-HHMMSS-HASH
    """
    now = datetime.utcnow()
    time_str = now.strftime("%Y%m%d-%H%M%S")

    # interval (biar token sama dalam 30 detik)
    interval_time = int(time.time() / INTERVAL)

    raw = str(interval_time) + SECRET_KEY
    hash_part = hashlib.sha256(raw.encode()).hexdigest()[:8]

    token = f"ATTEND-{time_str}-{hash_part}"
    return token


# 🔥 VALIDASI TOKEN (ANTI SHARE)
def validate_token(token):
    """
    Valid jika:
    - token sama dengan sekarang
    - atau token sebelumnya (toleransi delay)
    """
    try:
        parts = token.split("-")
        if len(parts) != 4:
            return False

        token_time_str = parts[1] + parts[2]
        token_time = datetime.strptime(token_time_str, "%Y%m%d%H%M%S")

        # 🔥 cek umur token (30 detik)
        if (datetime.utcnow() - token_time).total_seconds() > INTERVAL:
            return False

        # 🔥 cek hash
        current_interval = int(time.time() / INTERVAL)
        prev_interval = current_interval - 1

        valid_tokens = []

        for t in [current_interval, prev_interval]:
            raw = str(t) + SECRET_KEY
            hash_part = hashlib.sha256(raw.encode()).hexdigest()[:8]

            expected_token = f"ATTEND-{token_time.strftime('%Y%m%d-%H%M%S')}-{hash_part}"
            valid_tokens.append(expected_token)

        return token in valid_tokens

    except:
        return False


# 🔥 GENERATE QR (TIDAK KETIMPA)
def generate_qr(token):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{QR_FOLDER}/qr_{timestamp}.png"

    img = qrcode.make(token)
    img.save(filename)

    print(f"✅ QR code created: {filename}")
    return filename


# 🔥 START SESSION (UNTUK TEST / DEMO CLI)
def start_qr_session():
    """
    QR aktif 5 menit
    update tiap 30 detik
    """
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time

        if elapsed > SESSION_DURATION:
            print("⛔ Session ended! QR no longer valid.")
            break

        token = generate_token()
        generate_qr(token)

        print(f"🟢 Active Token: {token}")
        print(f"⏳ Remaining: {int(SESSION_DURATION - elapsed)} detik\n")

        time.sleep(INTERVAL)