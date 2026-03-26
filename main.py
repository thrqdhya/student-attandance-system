import requests
from qr_engine.token_generator import generate_qr
from qr_engine.qr_scanner import scan_qr

BASE_URL = "http://localhost:5001"

def main():
    # ---------------------------
    # 1. CREATE SESSION (ambil token dari backend)
    # ---------------------------
    response = requests.post(
        f"{BASE_URL}/api/session/create",
        json={"lecturer_id": 1}
    )

    data = response.json()

    if data["status"] != "success":
        print("Gagal buat session")
        return

    token = data["data"]["token_qr"]
    print("Token dari backend:", token)

    # ---------------------------
    # 2. GENERATE QR
    # ---------------------------
    qr_file = generate_qr(token)

    # ---------------------------
    # 3. SCAN QR (simulate)
    # ---------------------------
    scanned_token = scan_qr(qr_file)

    if not scanned_token:
        return

    # ---------------------------
    # 4. KIRIM KE BACKEND (absensi)
    # ---------------------------
    response = requests.post(
        f"{BASE_URL}/api/attendance/scan",
        json={
            "nim": "12345",
            "token_qr": scanned_token
        }
    )

    print("Response backend:")
    print(response.json())


if __name__ == "__main__":
    main()