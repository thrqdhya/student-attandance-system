import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
import os
import base64
from io import BytesIO
from PIL import Image, ImageTk
import threading
import time

API_BASE_URL = "http://127.0.0.1:8000"
STUDENT_CONFIG_FILE = "student_session.json"

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Attendance System")
        self.root.geometry("600x700")
        self.root.configure(bg="#f0f0f0")
        
        self.container = tk.Frame(self.root, bg="#f0f0f0")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.current_frame = None
        self.student_data = self.load_student_config()
        self.show_selection_screen()

    def load_student_config(self):
        if os.path.exists(STUDENT_CONFIG_FILE):
            try:
                with open(STUDENT_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None

    def save_student_config(self, nim, nama):
        data = {"nim": nim, "nama": nama}
        with open(STUDENT_CONFIG_FILE, 'w') as f:
            json.dump(data, f)
        self.student_data = data

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    def show_selection_screen(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.container, bg="#f0f0f0")
        self.current_frame.pack(fill="both", expand=True)
        
        tk.Label(self.current_frame, text="Attendance System", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=50)
        
        tk.Button(self.current_frame, text="Mode Dosen (Lecturer)", font=("Arial", 14), 
                  width=25, height=2, bg="#4CAF50", fg="white", 
                  command=self.show_lecturer_login).pack(pady=10)
        
        tk.Button(self.current_frame, text="Mode Mahasiswa (Student)", font=("Arial", 14), 
                  width=25, height=2, bg="#2196F3", fg="white",
                  command=self.handle_student_mode).pack(pady=10)

    # --- LECTURER MODE ---
    
    def show_lecturer_login(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.container, bg="#f0f0f0")
        self.current_frame.pack(fill="both", expand=True)
        
        tk.Label(self.current_frame, text="Lecturer Login", font=("Arial", 18, "bold"), bg="#f0f0f0").pack(pady=30)
        
        tk.Label(self.current_frame, text="Password:", bg="#f0f0f0").pack()
        self.pass_entry = tk.Entry(self.current_frame, show="*", font=("Arial", 12))
        self.pass_entry.pack(pady=5)
        self.pass_entry.bind('<Return>', lambda e: self.do_lecturer_login())
        
        tk.Button(self.current_frame, text="Login", command=self.do_lecturer_login, 
                  bg="#4CAF50", fg="white", width=15).pack(pady=20)
        
        tk.Button(self.current_frame, text="Back", command=self.show_selection_screen).pack()

    def do_lecturer_login(self):
        password = self.pass_entry.get()
        try:
            response = requests.post(f"{API_BASE_URL}/lecturer/login", json={"password": password})
            if response.status_code == 200:
                self.show_lecturer_dashboard()
            else:
                messagebox.showerror("Error", "Invalid Password")
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect to API: {e}")

    def show_lecturer_dashboard(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.container, bg="#f0f0f0")
        self.current_frame.pack(fill="both", expand=True)
        
        tk.Label(self.current_frame, text="Lecturer Dashboard", font=("Arial", 18, "bold"), bg="#f0f0f0").pack(pady=10)
        
        self.session_btn = tk.Button(self.current_frame, text="Start Attendance Session", 
                                     command=self.start_attendance_session, bg="#4CAF50", fg="white")
        self.session_btn.pack(pady=5)
        
        self.timer_label = tk.Label(self.current_frame, text="No Active Session", font=("Arial", 12), bg="#f0f0f0")
        self.timer_label.pack(pady=5)
        
        self.qr_label = tk.Label(self.current_frame, bg="#f0f0f0")
        self.qr_label.pack(pady=10)
        
        self.token_label = tk.Label(self.current_frame, text="", font=("Courier", 10), bg="#f0f0f0")
        self.token_label.pack()
        
        # Attendance List
        tk.Label(self.current_frame, text="Attendance List:", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=(10,0))
        self.tree = ttk.Treeview(self.current_frame, columns=("NIM", "Nama", "Time"), show="headings", height=8)
        self.tree.heading("NIM", text="NIM")
        self.tree.heading("Nama", text="Nama")
        self.tree.heading("Time", text="Time")
        self.tree.column("NIM", width=100)
        self.tree.column("Nama", width=200)
        self.tree.column("Time", width=150)
        self.tree.pack(pady=5, fill="x")
        
        tk.Button(self.current_frame, text="Logout", command=self.show_selection_screen).pack(pady=10)
        
        self.refresh_dashboard()

    def start_attendance_session(self):
        try:
            response = requests.post(f"{API_BASE_URL}/lecturer/start-session")
            if response.status_code == 200:
                messagebox.showinfo("Success", "Session started for 5 minutes")
                self.refresh_dashboard()
            else:
                messagebox.showerror("Error", "Failed to start session")
        except Exception as e:
            messagebox.showerror("Error", f"API Error: {e}")

    def refresh_dashboard(self):
        if not hasattr(self, 'current_frame') or not self.current_frame.winfo_exists():
            return

        try:
            # Get Status
            status_res = requests.get(f"{API_BASE_URL}/lecturer/status")
            if status_res.status_code == 200:
                status = status_res.json()
                if status.get("is_active"):
                    secs = status.get("remaining_seconds", 0)
                    mins, rem_secs = divmod(secs, 60)
                    self.timer_label.config(text=f"Time Remaining: {mins:02d}:{rem_secs:02d}", fg="red")
                    
                    # Update QR
                    qr_base64 = status.get("qr_code_base64")
                    if qr_base64:
                        img_data = base64.b64decode(qr_base64)
                        img = Image.open(BytesIO(img_data))
                        img = img.resize((200, 200))
                        photo = ImageTk.PhotoImage(img)
                        self.qr_label.config(image=photo)
                        self.qr_label.image = photo # Keep reference
                    
                    self.token_label.config(text=f"Token: {status.get('current_token')}")
                else:
                    self.timer_label.config(text="No Active Session", fg="black")
                    self.qr_label.config(image='')
                    self.token_label.config(text="")

            # Get Attendance List
            list_res = requests.get(f"{API_BASE_URL}/lecturer/attendance-list")
            if list_res.status_code == 200:
                data = list_res.json().get("data", [])
                # Clear existing
                for item in self.tree.get_children():
                    self.tree.delete(item)
                # Add new
                for row in data:
                    self.tree.insert("", "end", values=(row['nim'], row['nama'], row['timestamp']))
                    
        except Exception as e:
            print(f"Refresh error: {e}")
            
        # Schedule next refresh in 2 seconds
        self.root.after(2000, self.refresh_dashboard)

    # --- STUDENT MODE ---
    
    def handle_student_mode(self):
        if self.student_data:
            # Auto login if config exists
            self.show_student_dashboard()
        else:
            self.show_student_register()

    def show_student_register(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.container, bg="#f0f0f0")
        self.current_frame.pack(fill="both", expand=True)
        
        tk.Label(self.current_frame, text="Student Registration", font=("Arial", 18, "bold"), bg="#f0f0f0").pack(pady=30)
        
        tk.Label(self.current_frame, text="NIM:", bg="#f0f0f0").pack()
        self.nim_entry = tk.Entry(self.current_frame, font=("Arial", 12))
        self.nim_entry.pack(pady=5)
        
        tk.Label(self.current_frame, text="Full Name:", bg="#f0f0f0").pack()
        self.name_entry = tk.Entry(self.current_frame, font=("Arial", 12))
        self.name_entry.pack(pady=5)
        
        tk.Button(self.current_frame, text="Register", command=self.do_student_register, 
                  bg="#2196F3", fg="white", width=15).pack(pady=20)
        
        tk.Button(self.current_frame, text="Back", command=self.show_selection_screen).pack()

    def do_student_register(self):
        nim = self.nim_entry.get().strip()
        nama = self.name_entry.get().strip()
        
        if not nim or not nama:
            messagebox.showwarning("Warning", "Please fill all fields")
            return
            
        try:
            response = requests.post(f"{API_BASE_URL}/student/register", json={"nim": nim, "nama": nama})
            if response.status_code == 200:
                self.save_student_config(nim, nama)
                messagebox.showinfo("Success", "Registration successful!")
                self.show_student_dashboard()
            else:
                err = response.json().get("detail", "Registration failed")
                messagebox.showerror("Error", err)
        except Exception as e:
            messagebox.showerror("Error", f"API Error: {e}")

    def show_student_dashboard(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.container, bg="#f0f0f0")
        self.current_frame.pack(fill="both", expand=True)
        
        tk.Label(self.current_frame, text=f"Welcome, {self.student_data['nama']}", 
                 font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=20)
        tk.Label(self.current_frame, text=f"NIM: {self.student_data['nim']}", font=("Arial", 12), bg="#f0f0f0").pack()
        
        tk.Label(self.current_frame, text="\nScan QR Code / Enter Token:", font=("Arial", 12), bg="#f0f0f0").pack(pady=10)
        self.token_entry = tk.Entry(self.current_frame, font=("Arial", 14), width=30, justify="center")
        self.token_entry.pack(pady=5)
        self.token_entry.insert(0, "ATTEND-")
        
        tk.Button(self.current_frame, text="Submit Attendance", command=self.submit_attendance, 
                  bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=20, height=2).pack(pady=20)
        
        tk.Label(self.current_frame, text="(Note: In desktop mode, please type/paste the token from the lecturer screen)", 
                 font=("Arial", 8, "italic"), bg="#f0f0f0").pack()

        tk.Button(self.current_frame, text="Exit", command=self.show_selection_screen).pack(pady=30)

    def submit_attendance(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showwarning("Warning", "Please enter a token")
            return
            
        payload = {
            "nim": self.student_data['nim'],
            "nama": self.student_data['nama'],
            "token": token
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/submit-attendance", json=payload)
            if response.status_code == 200:
                messagebox.showinfo("Success", response.json().get("message"))
                self.token_entry.delete(0, tk.END)
                self.token_entry.insert(0, "ATTEND-")
            else:
                err = response.json().get("detail", "Attendance failed")
                messagebox.showerror("Error", err)
        except Exception as e:
            messagebox.showerror("Error", f"API Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()
