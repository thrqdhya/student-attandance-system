import requests

BASE_URL = "http://192.168.1.106:5001"  # 🔥 pakai IP kamu

def main():
    # 1. ambil QR terbaru
    res = requests.get(f"{BASE_URL}/api/session/1/refresh-qr")
    data = res.json()

    if data["status"] != "success":
        print("Gagal ambil QR")
        return

    token = data["token"]
    print("Token:", token)

    # 2. kirim absensi
    res = requests.post(
        f"{BASE_URL}/api/attendance/scan",
        json={
            "nim": "12345",
            "token_qr": token
        }
    )

    print("Response:")
    print(res.json())


if __name__ == "__main__":
    main()