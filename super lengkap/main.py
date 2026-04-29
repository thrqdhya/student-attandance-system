from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import csv
import os
import secrets
import time
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timedelta

import mysql.connector
from mysql.connector import Error

app = FastAPI(title="Student Attendance System API")

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'database': 'qr_db',
    'user': 'root',
    'password': 'oke'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Create students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                nim VARCHAR(20) PRIMARY KEY,
                nama VARCHAR(100) NOT NULL
            )
        """)
        # Create attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nim VARCHAR(20),
                nama VARCHAR(100),
                timestamp DATETIME,
                session_id VARCHAR(50),
                FOREIGN KEY (nim) REFERENCES students(nim)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

# Initialize database tables
init_db()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LECTURER_PASSWORD = "admin123"  # Simple password for lecturer
SESSION_DURATION_MINUTES = 5
TOKEN_EXPIRY_SECONDS = 30
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "students.csv"

# State
class SessionState:
    is_active = False
    start_time = 0
    session_id = ""  # Unique ID for each attendance session
    current_token = ""
    previous_token = ""  # Store previous token for transition tolerance
    last_token_update = 0

session = SessionState()

class AttendanceRecord(BaseModel):
    nim: str
    nama: str
    token: str

class StudentRegister(BaseModel):
    nim: str
    nama: str

class LoginRequest(BaseModel):
    password: str

def save_to_db(nim, nama, timestamp, session_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO attendance (nim, nama, timestamp, session_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (nim, nama, timestamp, session_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

def register_student_db(nim, nama):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Check if NIM already registered
        cursor.execute("SELECT nim FROM students WHERE nim = %s", (nim,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False
        
        query = "INSERT INTO students (nim, nama) VALUES (%s, %s)"
        cursor.execute(query, (nim, nama))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

def get_student_by_nim_db(nim):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nim, nama FROM students WHERE nim = %s", (nim,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        return student
    return None

def save_to_csv(nim, nama, timestamp, session_id):
    file_exists = os.path.isfile(ATTENDANCE_FILE)
    with open(ATTENDANCE_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['NIM', 'Nama', 'Timestamp', 'SessionID'])
        writer.writerow([nim, nama, timestamp, session_id])

def register_student_csv(nim, nama):
    file_exists = os.path.isfile(STUDENTS_FILE)
    # Check if NIM already registered
    if file_exists:
        with open(STUDENTS_FILE, mode='r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == nim:
                    return False
    
    with open(STUDENTS_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['NIM', 'Nama'])
        writer.writerow([nim, nama])
    return True

def get_student_by_nim(nim):
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['NIM'] == nim:
                    return row
    return None

def generate_dynamic_token():
    """
    Generates a token based on the format in memory.md:
    ATTEND-YYYYMMDD-HHMMSS-RAND
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_suffix = secrets.token_hex(2).upper()
    return f"ATTEND-{timestamp}-{random_suffix}"

def update_session_token():
    """Rotates the current token to previous and generates a new one."""
    session.previous_token = session.current_token
    session.current_token = generate_dynamic_token()
    session.last_token_update = time.time()

@app.get("/")
async def root():
    return {"message": "Welcome to Student Attendance System API"}

@app.post("/student/register")
async def register_student(student: StudentRegister):
    """
    Register a student for the first time.
    Saves to MySQL and CSV.
    """
    # Save to MySQL
    success = register_student_db(student.nim, student.nama)
    if not success:
        raise HTTPException(status_code=400, detail="NIM already registered in Database")
    
    # Also keep CSV for backup/offline
    register_student_csv(student.nim, student.nama)
    
    return {"status": "success", "message": f"Student {student.nim} registered successfully"}

@app.get("/student/profile/{nim}")
async def get_profile(nim: str):
    """
    Used for auto-login on the student app.
    Checks if NIM exists in MySQL.
    """
    student = get_student_by_nim_db(nim)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.post("/lecturer/login")
async def lecturer_login(req: LoginRequest):
    if req.password == LECTURER_PASSWORD:
        return {"status": "success", "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")

@app.post("/lecturer/start-session")
async def start_session():
    session.is_active = True
    session.start_time = time.time()
    session.session_id = datetime.now().strftime("%Y%m%d-%H%M")
    session.previous_token = ""
    session.current_token = generate_dynamic_token()
    session.last_token_update = time.time()
    return {
        "status": "success", 
        "message": f"Attendance session {session.session_id} started for 5 minutes"
    }

@app.get("/lecturer/status")
async def get_status():
    if not session.is_active:
        return {"is_active": False}
    
    elapsed = time.time() - session.start_time
    remaining = max(0, (SESSION_DURATION_MINUTES * 60) - elapsed)
    
    if remaining <= 0:
        session.is_active = False
        return {"is_active": False, "message": "Session expired"}

    # Update token if 30 seconds passed
    if time.time() - session.last_token_update >= TOKEN_EXPIRY_SECONDS:
        update_session_token()

    # Generate QR Base64
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(session.current_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return {
        "is_active": True,
        "remaining_seconds": int(remaining),
        "current_token": session.current_token,
        "qr_code_base64": img_str
    }

@app.post("/submit-attendance")
async def submit_attendance(record: AttendanceRecord):
    if not session.is_active:
        raise HTTPException(status_code=400, detail="No active attendance session")
    
    # Validate token (Allow current OR previous token for 30s boundary tolerance)
    valid_tokens = [session.current_token, session.previous_token]
    if record.token not in valid_tokens or not record.token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # 1. NEW: Validate if NIM is registered (Requirement from memory.md: "NIM terdaftar")
    student = get_student_by_nim_db(record.nim)
    if not student:
        raise HTTPException(status_code=404, detail="NIM not registered. Please register first.")
    
    # Ensure the name matches the registered NIM to prevent identity fraud
    if student['nama'].lower() != record.nama.lower():
        raise HTTPException(status_code=400, detail="NIM and Name do not match our records")

    # 2. Check if already recorded in current session via MySQL
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM attendance WHERE nim = %s AND session_id = %s", (record.nim, session.session_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="NIM already recorded for this session")
        cursor.close()
        conn.close()

    timestamp = datetime.now()
    # Save to MySQL
    save_to_db(record.nim, record.nama, timestamp, session.session_id)
    
    # Also save to CSV for backup
    save_to_csv(record.nim, record.nama, timestamp.strftime("%Y-%m-%d %H:%M:%S"), session.session_id)
    
    return {"status": "success", "message": f"Attendance recorded for {record.nim}"}

@app.post("/lecturer/reset-data")
async def reset_data():
    """Endpoint to clear MySQL and CSV data (use with caution)."""
    # Clear MySQL
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE attendance")
        cursor.execute("TRUNCATE TABLE students")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        cursor.close()
        conn.close()

    # Clear CSV
    if os.path.exists(ATTENDANCE_FILE):
        os.remove(ATTENDANCE_FILE)
    if os.path.exists(STUDENTS_FILE):
        os.remove(STUDENTS_FILE)
    return {"status": "success", "message": "All database and CSV data cleared"}

@app.get("/lecturer/attendance-list")
async def get_attendance():
    """Get attendance list from MySQL."""
    data = []
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nim, nama, timestamp, session_id FROM attendance")
        data = cursor.fetchall()
        # Convert datetime to string for JSON
        for row in data:
            if row['timestamp']:
                row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        cursor.close()
        conn.close()
    return {"data": data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
