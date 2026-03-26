# Flask Backend API

Backend untuk aplikasi QR Keamanan menggunakan Flask.

## Prasyarat

- Python 3.8+
- pip

## Cara Menjalankan

1. Masuk ke folder backend:
   ```bash
   cd backend
   ```

2. Buat virtual environment (jika belum ada):
   ```bash
   python3 -m venv venv
   ```

3. Aktifkan virtual environment:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

4. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```

5. Jalankan aplikasi:
   ```bash
   python app.py
   ```

Aplikasi akan berjalan di `http://localhost:5000`.

## Endpoint Utama

- `GET /`: Mengecek status API.
- `GET /api/health`: Health check API.
