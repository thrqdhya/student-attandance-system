from pyzbar.pyzbar import decode
from PIL import Image
import cv2
import requests
import os

# 🔥 GANTI kalau port/backend kamu beda
API_URL = "http://127.0.0.1:5001/api/attendance/scan"

# ---------------- AUTOMATIC QR DETECTION ----------------
def find_latest_qr_file():
    """
    Cari file QR PNG terbaru di folder saat ini
    """
    png_files = [f for f in os.listdir('.') if f.endswith('.png') and f.startswith('qr_')]
    if not png_files:
        print("❌ Tidak ada file QR PNG di folder ini")
        return None
    # ambil yang terbaru (urutan abjad/token biasanya cukup)
    latest_file = sorted(png_files)[-1]
    print(f"📂 QR file otomatis terdeteksi: {latest_file}")
    return latest_file

# ---------------- SCAN DARI FILE ----------------
def scan_qr(qr_file):
    try:
        img = Image.open(qr_file)
        result = decode(img)

        if result:
            token = result[0].data.decode()
            print("📷 Scan Result:", token)
            return token
        else:
            print("❌ QR tidak terbaca")
            return None

    except Exception as e:
        print("❌ Error scan:", e)
        return None

# ---------------- SCAN DARI KAMERA (opsional) ----------------
def scan_qr_camera():
    cap = cv2.VideoCapture(0)
    print("📷 Kamera aktif... tekan ESC untuk keluar")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        decoded = decode(frame)
        for obj in decoded:
            token = obj.data.decode("utf-8")
            print("✅ QR Detected:", token)
            cap.release()
            cv2.destroyAllWindows()
            return token

        cv2.imshow("QR Scanner", frame)

        if cv2.waitKey(1) == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# ---------------- KIRIM KE BACKEND ----------------
def send_to_backend(student_nim, token):
    try:
        response = requests.post(API_URL, json={
            "nim": student_nim,
            "token_qr": token
        })
        data = response.json()
        print("🌐 RESPONSE:", data)

        if response.status_code == 200:
            print("🎉 ABSENSI BERHASIL")
            return True
        else:
            print("🚫 ABSENSI GAGAL:", data.get("message"))
            return False

    except Exception as e:
        print("❌ ERROR koneksi ke server:", e)
        return False

# ---------------- FULL FLOW ----------------
def scan_for_attendance(student_nim, use_camera=False):
    """
    Flow lengkap:
    otomatis detect QR PNG → scan → kirim ke backend
    """
    if use_camera:
        token = scan_qr_camera()
    else:
        qr_file = find_latest_qr_file()
        if not qr_file:
            return False
        token = scan_qr(qr_file)

    if not token:
        print("❌ Tidak ada token atau QR invalid")
        return False

    return send_to_backend(student_nim, token)

# ---------------- TEST MANUAL ----------------
if __name__ == "__main__":
    print("===== QR ATTENDANCE SCANNER =====")

    student_nim = input("Masukkan NIM: ")

    mode = input("Pilih mode (1 = Kamera, 2 = File Otomatis PNG): ")

    if mode == "1":
        scan_for_attendance(student_nim, use_camera=True)
    else:
        scan_for_attendance(student_nim, use_camera=False)