Student Attendance System
1️⃣ Tujuan Aplikasi
Membuat sistem absensi mahasiswa berbasis GUI menggunakan Python, di mana:
•	Mahasiswa melakukan absensi secara mandiri
•	Menggunakan QR Code dinamis berbasis waktu
•	Dirancang untuk mengurangi kecurangan
•	Tidak memerlukan internet / web
2️⃣ Konsep Umum
Aplikasi terdiri dari satu program Python dengan dua mode pengguna:
Mode Dosen
Digunakan untuk:
•	Membuka sesi absensi
•	Menghasilkan dan menampilkan QR code
•	Memantau mahasiswa yang sudah absen
Mode Mahasiswa
Digunakan untuk:
•	Mengidentifikasi mahasiswa (NIM & Nama sudah terdaftar)
•	Melakukan scan QR code dari aplikasi
•	Melakukan absensi satu kali per sesi
3️⃣ Mekanisme QR Code
🔹 QR Code Dinamis (Time-Based Token)
•	QR code berisi token unik + waktu
•	QR berubah otomatis setiap 30 detik
•	Token yang sudah kedaluwarsa tidak dapat digunakan
📌 Contoh isi QR:
ATTEND-20260210-083000-X7B9

4️⃣ Alur Absensi
⏱️ Waktu Absensi : Sesi absensi dibuka selama 5 menit, dan QR code terus di perbarui setiap 30 detik. Setelah waktu habis sistem menutup absensi otomatis
1.	Dosen memilih Mode Dosen
2.	Dosen klik Start Attendance
3.	Sistem:
•	Menghasilkan QR code
•	Menampilkan QR di layar (proyektor)
•	Menjalankan timer
4.	Mahasiswa:
•	Masuk Mode Mahasiswa
•	Identitas sudah terdaftar di aplikasi
•	Scan QR code aktif
5.	Sistem melakukan validasi:
•	Token QR masih berlaku
•	Mahasiswa belum absen
6.	Jika valid → absensi dicatat
7.	Jika tidak valid → ditolak

5️⃣ Aturan Keamanan (Anti-Curang)
🔐 Aturan Utama
•	1 mahasiswa (1 NIM) hanya bisa absen 1 kali per sesi
•	Absensi terikat pada NIM, bukan QR code
•	QR code lama atau dibagikan tidak berlaku
🔐 Validasi Sistem
•	Token QR masih aktif
•	NIM terdaftar
•	NIM belum pernah absen pada sesi tersebut
🔹 Alur Login Mahasiswa
1.	Saat aplikasi pertama kali dijalankan:
o	Sistem mengecek apakah NIM sudah tersimpan di aplikasi
2.	Jika belum ada NIM:
o	Mahasiswa diminta memasukkan NIM
o	Sistem memverifikasi NIM dari data mahasiswa
3.	Jika NIM valid:
o	NIM dan nama mahasiswa disimpan secara lokal
o	Login berhasil
4.	Pada penggunaan berikutnya:
o	Aplikasi login otomatis
o	Tidak ada menu ganti akun
📌 Dengan mekanisme ini, satu aplikasi tidak dapat digunakan untuk lebih dari satu mahasiswa.
🔹 Mekanisme Login Dosen
1.	 Dosen login menggunakan:
•	Username & password
atau
•	Password saja (opsi sederhana)
2.	Data login disimpan secara lokal (offline)

6️⃣Teknologi yang Digunakan
•	Python
•	Tkinter (GUI)
•	qrcode (generate QR)
•	Pillow (PIL) (tampilkan QR)
•	CSV file (penyimpanan data)
•	Sistem berjalan offline

7️⃣ Kelebihan Sistem
•	Tidak membutuhkan internet
•	Menggunakan konsep keamanan berbasis waktu
•	Meminimalkan kecurangan
•	Cocok untuk mata kuliah Görsel Programlama
•	Mudah dikembangkan lebih lanjut



