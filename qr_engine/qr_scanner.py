# scanner_gui_auto_qr.py
import sys
import os
import io
import requests
from pyzbar.pyzbar import decode
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox

# sys.path fix supaya bisa import validate_token
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from qr_engine.token_generator import validate_token
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from token_generator import validate_token


class QRScannerApp:
    def __init__(self, master, student_id, qr_url, backend_url):
        self.master = master
        self.master.title("QR Attendance Scanner")
        self.student_id = student_id
        self.qr_url = qr_url        # URL untuk ambil QR terbaru
        self.backend_url = backend_url

        # Placeholder untuk gambar QR
        self.img = None
        self.tk_img = None

        self.label_img = tk.Label(master)
        self.label_img.pack(pady=10)

        # Tombol load QR dari backend
        self.btn_load_qr = tk.Button(master, text="Load Latest QR", command=self.load_qr)
        self.btn_load_qr.pack(pady=5)

        # Tombol scan
        self.btn_scan = tk.Button(master, text="Scan QR", command=self.scan_qr, state=tk.DISABLED)
        self.btn_scan.pack(pady=5)

        # Label hasil
        self.result_label = tk.Label(master, text="", font=("Arial", 16, "bold"))
        self.result_label.pack(pady=10)

        # Tombol HADIR (disabled awal)
        self.btn_hadir = tk.Button(master, text="HADIR", command=self.mark_attendance, state=tk.DISABLED)
        self.btn_hadir.pack(pady=5)

        self.scanned_token = None

    def load_qr(self):
        """
        Download QR image terbaru dari backend
        """
        try:
            resp = requests.get(self.qr_url)
            if resp.status_code != 200:
                messagebox.showerror("Error", f"Cannot load QR: {resp.status_code}")
                return

            img_bytes = io.BytesIO(resp.content)
            self.img = Image.open(img_bytes)
            self.tk_img = ImageTk.PhotoImage(self.img)
            self.label_img.config(image=self.tk_img)

            self.result_label.config(text="QR Loaded. Click Scan QR", fg="blue")
            self.btn_scan.config(state=tk.NORMAL)
            self.btn_hadir.config(state=tk.DISABLED)
            self.scanned_token = None

        except Exception as e:
            messagebox.showerror("Error", f"Cannot load QR: {e}")

    def scan_qr(self):
        """
        Scan QR + validasi
        """
        if self.img is None:
            messagebox.showwarning("Warning", "Load QR first!")
            return

        try:
            result = decode(self.img)
            if not result:
                self.result_label.config(text="❌ QR cannot be scanned", fg="red")
                return

            token = result[0].data.decode()
            self.scanned_token = token
            print("📷 Scan result:", token)

            if validate_token(token):
                self.result_label.config(text="✅ HADIR (click button to confirm)", fg="green")
                self.btn_hadir.config(state=tk.NORMAL)
            else:
                self.result_label.config(text="⛔ TOKEN INVALID / EXPIRED", fg="red")
                self.btn_hadir.config(state=tk.DISABLED)
                messagebox.showwarning("Attendance", "Token invalid or expired!")

        except Exception as e:
            self.result_label.config(text=f"❌ Error: {e}", fg="red")
            print("❌ Error while scanning QR:", e)

    def mark_attendance(self):
        """
        Kirim token + student_id ke backend
        """
        if not self.scanned_token:
            messagebox.showerror("Error", "No token scanned")
            return

        payload = {
            "nim": self.student_id,
            "token_qr": self.scanned_token
        }

        try:
            response = requests.post(self.backend_url, json=payload)
            data = response.json()

            if data.get("status") == "success":
                messagebox.showinfo("Attendance", f"🎓 Student {self.student_id} successfully signed in!")
                self.btn_hadir.config(state=tk.DISABLED)
                self.result_label.config(text="✅ Attendance Recorded", fg="green")
            else:
                messagebox.showerror("Attendance Failed", data.get("message", "Unknown error"))

        except Exception as e:
            messagebox.showerror("Error", f"Cannot connect to backend: {e}")


if __name__ == "__main__":
    student_id = "12345"
    qr_url = "http://127.0.0.1:5001/static/qr.png"  # endpoint QR terbaru
    backend_url = "http://127.0.0.1:5001/api/attendance/scan"

    root = tk.Tk()
    app = QRScannerApp(root, student_id, qr_url, backend_url)
    root.mainloop()