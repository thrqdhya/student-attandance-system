import tkinter as tk
from ui.student_ui import StudentUI
from ui.lecturer_ui import LecturerUI

def mode_selection():
    root = tk.Tk()
    root.title("Student Attendance System")
    root.geometry("300x200")

    tk.Label(root, text="Select Mode", font=("Arial", 16)).pack(pady=20)

    tk.Button(root, text="Student", width=20, command=lambda: open_student(root)).pack(pady=10)
    tk.Button(root, text="Lecturer", width=20, command=lambda: open_lecturer(root)).pack(pady=10)

    root.mainloop()

def open_student(root):
    root.destroy()
    root = tk.Tk()
    StudentUI(root)
    root.mainloop()

def open_lecturer(root):
    root.destroy()
    root = tk.Tk()
    # For prototype, use a fixed lecturer_id
    LecturerUI(root, lecturer_id="L001")
    root.mainloop()