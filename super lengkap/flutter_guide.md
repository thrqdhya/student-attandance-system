# Panduan Lengkap Integrasi Flutter dengan FastAPI (Sistem Absensi)

Dokumen ini adalah panduan komprehensif untuk mengembangkan aplikasi mobile **Flutter** (khusus Mahasiswa) yang terhubung ke backend FastAPI. Panduan ini mencakup manajemen sesi lokal, integrasi API, dan pemindaian QR Code.

---

## 1. Persiapan & Dependensi

Tambahkan package berikut di file `pubspec.yaml` Anda:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0                # Untuk request API ke backend
  shared_preferences: ^2.2.2  # Untuk menyimpan data NIM secara lokal (Auto-login)
  mobile_scanner: ^3.5.2      # Untuk memindai QR Code dari layar dosen
```

Lalu jalankan perintah:
```bash
flutter pub get
```

---

## 2. Konfigurasi Base URL

**PENTING**: Karena backend dijalankan secara lokal (localhost), Anda tidak bisa menggunakan `http://localhost:8000` di dalam aplikasi mobile (kecuali di iOS Simulator).

Buat file konfigurasi (misal: `lib/core/config.dart`):

```dart
// lib/core/config.dart
class AppConfig {
  // Jika menggunakan Emulator Android:
  static const String baseUrl = "http://10.0.2.2:8000"; 
  
  // Jika menggunakan iOS Simulator:
  // static const String baseUrl = "http://127.0.0.1:8000";
  
  // Jika menggunakan HP Fisik (Ganti dengan IP IPv4 WiFi Laptop Anda):
  // static const String baseUrl = "http://192.168.1.15:8000";
}
```

---

## 3. Manajemen Sesi (Auto-Login)

Aplikasi mahasiswa dirancang agar **hanya login satu kali**. Gunakan `SharedPreferences` untuk menyimpan data mahasiswa secara lokal.

```dart
// lib/services/session_service.dart
import 'package:shared_preferences/shared_preferences.dart';

class SessionService {
  static const String _keyNim = 'student_nim';
  static const String _keyNama = 'student_nama';

  // Simpan data setelah registrasi berhasil
  static Future<void> saveStudentSession(String nim, String nama) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyNim, nim);
    await prefs.setString(_keyNama, nama);
  }

  // Cek apakah mahasiswa sudah pernah login/registrasi
  static Future<Map<String, String>?> getStudentSession() async {
    final prefs = await SharedPreferences.getInstance();
    final nim = prefs.getString(_keyNim);
    final nama = prefs.getString(_keyNama);

    if (nim != null && nama != null) {
      return {'nim': nim, 'nama': nama};
    }
    return null; // Belum login
  }

  // Logout (Opsional, jika ingin mereset aplikasi)
  static Future<void> clearSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}
```

---

## 4. Implementasi API (Dengan Error Handling)

Berikut adalah contoh layanan API (`lib/services/api_service.dart`) yang sudah dilengkapi dengan notifikasi (Snackbar) untuk feedback ke pengguna.

```dart
// lib/services/api_service.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import 'session_service.dart';

class ApiService {
  
  // A. Registrasi Mahasiswa
  static Future<bool> registerStudent(BuildContext context, String nim, String nama) async {
    final url = Uri.parse("${AppConfig.baseUrl}/student/register");
    
    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"nim": nim, "nama": nama}),
      );

      if (response.statusCode == 200) {
        // Simpan sesi secara lokal jika sukses
        await SessionService.saveStudentSession(nim, nama);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Registrasi Berhasil!"), backgroundColor: Colors.green),
        );
        return true;
      } else {
        final error = jsonDecode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error['detail'] ?? "Registrasi Gagal"), backgroundColor: Colors.red),
        );
        return false;
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error Koneksi: $e"), backgroundColor: Colors.red),
      );
      return false;
    }
  }

  // B. Submit Absensi (Dari hasil Scan QR)
  static Future<bool> submitAttendance(BuildContext context, String token) async {
    // Ambil data mahasiswa dari penyimpanan lokal
    final session = await SessionService.getStudentSession();
    if (session == null) return false;

    final url = Uri.parse("${AppConfig.baseUrl}/submit-attendance");

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "nim": session['nim'],
          "nama": session['nama'],
          "token": token,
        }),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Absensi Berhasil Tercatat!"), backgroundColor: Colors.green),
        );
        return true;
      } else {
        final error = jsonDecode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error['detail'] ?? "Gagal Absen"), backgroundColor: Colors.red),
        );
        return false;
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error Koneksi Server"), backgroundColor: Colors.red),
      );
      return false;
    }
  }
}
```

---

## 5. Implementasi QR Scanner

Berikut adalah contoh halaman Scanner menggunakan package `mobile_scanner`. Halaman ini akan terbuka setelah mahasiswa berhasil masuk ke dashboard.

```dart
// lib/screens/scanner_screen.dart
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/api_service.dart';

class ScannerScreen extends StatefulWidget {
  @override
  _ScannerScreenState createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  bool isProcessing = false; // Mencegah scan ganda

  void _onDetect(BarcodeCapture capture) async {
    if (isProcessing) return;

    final List<Barcode> barcodes = capture.barcodes;
    if (barcodes.isNotEmpty) {
      final String? token = barcodes.first.rawValue;
      
      if (token != null && token.startsWith("ATTEND-")) {
        setState(() => isProcessing = true);
        
        // Jeda sejenak atau tampilkan loading
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => Center(child: CircularProgressIndicator()),
        );

        // Submit absensi ke API
        bool success = await ApiService.submitAttendance(context, token);
        
        // Tutup dialog loading
        Navigator.pop(context);

        // Jika sukses, kembali ke dashboard
        if (success) {
          Navigator.pop(context);
        } else {
          // Beri jeda sebelum bisa scan lagi jika gagal
          await Future.delayed(Duration(seconds: 2));
          setState(() => isProcessing = false);
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("QR Code Tidak Valid!"), backgroundColor: Colors.orange),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Scan QR Absensi")),
      body: MobileScanner(
        onDetect: _onDetect,
      ),
    );
  }
}
```

---

## 6. Alur Aplikasi yang Disarankan (App Flow)

1. **Splash Screen**:
   - Panggil `SessionService.getStudentSession()`.
   - Jika `null` -> Arahkan ke **Halaman Registrasi**.
   - Jika ada isinya -> Arahkan ke **Halaman Dashboard**.
2. **Halaman Registrasi**:
   - Form input NIM dan Nama.
   - Panggil `ApiService.registerStudent()`.
   - Jika sukses -> Arahkan ke **Halaman Dashboard**.
3. **Halaman Dashboard**:
   - Tampilkan informasi mahasiswa (NIM & Nama) dari lokal.
   - Tombol "Scan QR Code" -> Membuka **Scanner Screen**.
4. **Scanner Screen**:
   - Kamera memindai layar dosen.
   - Memanggil `ApiService.submitAttendance()`.

---

## 7. Troubleshooting & Tips

- **Android Cleartext Traffic**: Jika menggunakan HTTP biasa di HP Android fisik, tambahkan `android:usesCleartextTraffic="true"` di dalam file `android/app/src/main/AndroidManifest.xml` pada tag `<application>`.
- **Izin Kamera**: Pastikan Anda sudah menambahkan izin kamera di `AndroidManifest.xml` (Android) dan `Info.plist` (iOS) untuk menggunakan scanner.
  - Android: `<uses-permission android:name="android.permission.CAMERA" />`
  - iOS: `<key>NSCameraUsageDescription</key><string>Aplikasi membutuhkan kamera untuk scan QR</string>`
- **Kesalahan NIM/Nama**: Backend akan menolak (Error 400) jika Nama tidak cocok dengan NIM yang sudah terdaftar. Hal ini untuk mencegah penitipan absen ke teman.
