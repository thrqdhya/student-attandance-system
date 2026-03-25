import tkinter as tk
from backend.lecturer import create_session

class LecturerUI:
    def __init__(self, root, lecturer_id):
        self.root = root
        self.lecturer_id = lecturer_id
        self.root.title("Student Attendance System - Lecturer")
        self.root.geometry("400x400")
        self.build_dashboard()

    def build_dashboard(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        tk.Label(self.root, text="Lecturer Dashboard", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.root, text=f"Lecturer ID: {self.lecturer_id}").pack(pady=5)

        tk.Button(self.root, text="Create Session", command=self.create_new_session).pack(pady=20)

        self.qr_label = tk.Label(self.root, text="QR Token will appear here", fg="blue", font=("Arial", 12))
        self.qr_label.pack(pady=10)

    def create_new_session(self):
        token = create_session(self.lecturer_id)
        self.qr_label.config(text=f"QR Token: {token}")