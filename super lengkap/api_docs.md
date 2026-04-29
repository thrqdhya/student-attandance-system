# API Documentation - Student Attendance System

Sistem absensi mahasiswa berbasis QR Code dinamis yang berjalan offline menggunakan FastAPI.

## Base URL
`http://127.0.0.1:8000`

---

## 👨‍🏫 Mode Dosen (Lecturer)

### 1. Login Dosen
Digunakan untuk masuk ke sistem dosen.
- **Endpoint**: `POST /lecturer/login`
- **Request Body**:
  ```json
  {
    "password": "admin123"
  }
  ```
- **Response**: `200 OK` jika berhasil.

### 2. Buka Sesi Absensi
Membuka sesi absensi selama 5 menit. Setiap sesi memiliki `SessionID` unik berbasis waktu.
- **Endpoint**: `POST /lecturer/start-session`
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Attendance session 20260428-1530 started for 5 minutes"
  }
  ```

### 3. Status Sesi & QR Code
Mengambil status sesi aktif, waktu tersisa, dan QR code terbaru. QR Code berubah setiap 30 detik.
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

### 4. Lihat Daftar Hadir
Melihat daftar mahasiswa yang sudah absen dari file CSV.
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
Menghapus seluruh data absensi dan data mahasiswa (CSV). Gunakan dengan hati-hati.
- **Endpoint**: `POST /lecturer/reset-data`
- **Response**:
  ```json
  {
    "status": "success",
    "message": "All data cleared"
  }
  ```

---

## 🎓 Mode Mahasiswa (Student)

### 1. Registrasi Mahasiswa
Pendaftaran NIM dan Nama pada penggunaan pertama aplikasi.
- **Endpoint**: `POST /student/register`
- **Request Body**:
  ```json
  {
    "nim": "220101001",
    "nama": "Budi Santoso"
  }
  ```

### 2. Cek Profil (Auto-Login)
Mengecek apakah NIM sudah terdaftar untuk auto-login.
- **Endpoint**: `GET /student/profile/{nim}`
- **Response**: `200 OK` (Data Mahasiswa) atau `404 Not Found`.

### 3. Kirim Absensi (Scan QR)
Mengirim data absensi setelah berhasil scan QR code.
- **Endpoint**: `POST /submit-attendance`
- **Request Body**:
  ```json
  {
    "nim": "220101001",
    "nama": "Budi Santoso",
    "token": "ATTEND-20260428-153045-A1B2"
  }
  ```
- **Aturan**:
  - Token harus aktif (berlaku 30 detik + toleransi transisi).
  - NIM belum pernah absen pada sesi tersebut.

---

## 🛠️ Dokumentasi Interaktif (Swagger)
FastAPI menyediakan dokumentasi interaktif yang bisa langsung dicoba melalui browser:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
