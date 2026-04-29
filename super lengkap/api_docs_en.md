# API Documentation - Student Attendance System

A dynamic QR code-based student attendance system running offline using FastAPI.

## Base URL
`http://127.0.0.1:8000`

---

## 👨‍🏫 Lecturer Mode

### 1. Lecturer Login
Used to access the lecturer system.
- **Endpoint**: `POST /lecturer/login`
- **Request Body**:
  ```json
  {
    "password": "admin123"
  }
  ```
- **Response**: `200 OK` on success.

### 2. Start Attendance Session
Opens an attendance session for 5 minutes. Each session has a unique time-based `SessionID`.
- **Endpoint**: `POST /lecturer/start-session`
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Attendance session 20260428-1530 started for 5 minutes"
  }
  ```

### 3. Session Status & QR Code
Retrieves active session status, remaining time, and the latest QR code. The QR Code rotates every 30 seconds.
- **Endpoint**: `GET /lecturer/status`
- **Response**:
  ```json
  {
    "is_active": true,
    "remaining_seconds": 285,
    "current_token": "ATTEND-20260428-153045-A1B2",
    "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
  }
  ```

### 4. View Attendance List
Retrieves the list of students who have attended from the CSV file.
- **Endpoint**: `GET /lecturer/attendance-list`
- **Response**:
  ```json
  {
    "data": [
      {
        "NIM": "220101001",
        "Nama": "Budi Santoso",
        "Timestamp": "2026-04-28 15:35:10",
        "SessionID": "20260428-1530"
      }
    ]
  }
  ```

### 5. Reset Data
Clears all attendance and student data (CSV files). Use with caution.
- **Endpoint**: `POST /lecturer/reset-data`
- **Response**:
  ```json
  {
    "status": "success",
    "message": "All data cleared"
  }
  ```

---

## 🎓 Student Mode

### 1. Student Registration
Register NIM and Name on the first use of the application.
- **Endpoint**: `POST /student/register`
- **Request Body**:
  ```json
  {
    "nim": "220101001",
    "nama": "Budi Santoso"
  }
  ```

### 2. Profile Check (Auto-Login)
Checks if the NIM is already registered for auto-login purposes.
- **Endpoint**: `GET /student/profile/{nim}`
- **Response**: `200 OK` (Student Data) or `404 Not Found`.

### 3. Submit Attendance (Scan QR)
Submits attendance data after successfully scanning the QR code.
- **Endpoint**: `POST /submit-attendance`
- **Request Body**:
  ```json
  {
    "nim": "220101001",
    "nama": "Budi Santoso",
    "token": "ATTEND-20260428-153045-A1B2"
  }
  ```
- **Rules**:
  - Token must be active (valid for 30 seconds + transition tolerance).
  - NIM must not have already attended for the current session.

---

## 🛠️ Interactive Documentation (Swagger)
FastAPI provides interactive documentation that can be tested directly via the browser:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
