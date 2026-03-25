import tkinter as tk
from tkinter import messagebox
from backend.student import validate_nim
from backend.attendance import save_attendance
from database.db_helper import query_db

class StudentUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Attendance System - Student")
        self.root.geometry("400x300")
        self.build_login()

    def build_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        tk.Label(self.root, text="Student Login", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.root, text="Enter NIM:").pack(pady=5)
        self.nim_entry = tk.Entry(self.root)
        self.nim_entry.pack(pady=5)

        tk.Button(self.root, text="Login", command=self.login_student).pack(pady=20)

    def login_student(self):
        nim = self.nim_entry.get()
        if not nim:
            messagebox.showerror("Error", "Please enter NIM")
            return
        if validate_nim(nim):
            self.build_scan_page(nim)
        else:
            messagebox.showerror("Error", "NIM not found")

    def build_scan_page(self, nim):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        tk.Label(self.root, text="Scan QR Code", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.root, text=f"NIM: {nim}").pack(pady=5)

        # For prototype, simulate QR scan by session ID input
        tk.Label(self.root, text="Enter Session ID (simulate QR scan):").pack(pady=5)
        self.session_entry = tk.Entry(self.root)
        self.session_entry.pack(pady=5)

        tk.Button(self.root, text="Submit Attendance", command=lambda: self.scan_qr(nim)).pack(pady=20)

    def scan_qr(self, nim):
        session_id = self.session_entry.get()
        if not session_id:
            messagebox.showerror("Error", "Please enter Session ID")
            return
        
        # Check if session exists
        session = query_db("SELECT * FROM sessions WHERE session_id=?", (session_id,))
        if not session:
            messagebox.showerror("Error", "Session not found")
            return

        # Save attendance
        save_attendance(nim, session_id)
        messagebox.showinfo("Success", "Attendance recorded!")