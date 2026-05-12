import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'device_service.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bartın Uni Attendance',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Segoe UI',
        primaryColor: const Color(0xFF0b1a58),
      ),
      home: const LoginPage(),
    );
  }
}

//////////////////////////////////////////////////
// 🎨 1. LOGIN PAGE
//////////////////////////////////////////////////

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final TextEditingController nameController = TextEditingController();
  final TextEditingController nimController = TextEditingController();
  bool isLoading = false;

  // 🔥 LOGIKA LOGIN BARU: Tembak API untuk ambil Profil & Jadwal Kuliah
  Future<void> login() async {
    String name = nameController.text.trim();
    String nim = nimController.text.trim();

    if (name.isEmpty || nim.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Please enter both Full Name and Student Number"),
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }

    setState(() => isLoading = true);

    try {
      final url = Uri.parse("http://192.168.1.105:5001/api/student/login");
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"nim": nim}), // Backend kita hanya butuh NIM untuk cek DB
      );

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        final studentData = result['data'];

        // Jika berhasil, pindah ke halaman Dashboard dengan membawa data
        if (mounted) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => DashboardPage(
                studentData: studentData,
              ),
            ),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text("Student not found in database!"),
              backgroundColor: Colors.redAccent,
            ),
          );
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Connection error to server"),
          backgroundColor: Colors.redAccent,
        ),
      );
    } finally {
      if (mounted) setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0b1a58),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 40),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    "Student Portal",
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 30),

                  Container(
                    width: 140,
                    height: 160,
                    decoration: BoxDecoration(
                      color: const Color(0xFF3b82f6),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 20, offset: const Offset(0, 10)),
                      ],
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                          child: const Icon(Icons.school, size: 45, color: Color(0xFF1E293B)),
                        ),
                        const SizedBox(height: 10),
                        const Text("Student", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 40),

                  // 🔥 INPUT FULL NAME
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text("Full Name", style: TextStyle(color: Colors.white, fontSize: 14)),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                    child: TextField(
                      controller: nameController,
                      style: const TextStyle(color: Colors.black, fontSize: 16),
                      decoration: const InputDecoration(
                        hintText: "Enter your full name...",
                        hintStyle: TextStyle(color: Colors.grey),
                        prefixIcon: Icon(Icons.person_outline, color: Colors.grey),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(vertical: 15),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // 🔥 INPUT STUDENT NUMBER
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text("Student Number (NIM)", style: TextStyle(color: Colors.white, fontSize: 14)),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                    child: TextField(
                      controller: nimController,
                      keyboardType: TextInputType.number,
                      style: const TextStyle(color: Colors.black, fontSize: 16),
                      decoration: const InputDecoration(
                        hintText: "Enter your NIM...",
                        hintStyle: TextStyle(color: Colors.grey),
                        prefixIcon: Icon(Icons.badge, color: Colors.grey),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(vertical: 15),
                      ),
                    ),
                  ),
                  const SizedBox(height: 30),

                  SizedBox(
                    width: double.infinity,
                    height: 55,
                    child: ElevatedButton(
                      onPressed: isLoading ? null : login,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF3b82f6),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: isLoading
                          ? const CircularProgressIndicator(color: Colors.white)
                          : const Text("Log in", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

//////////////////////////////////////////////////
// 📊 2. DASHBOARD PAGE (BARU!)
//////////////////////////////////////////////////

class DashboardPage extends StatelessWidget {
  final Map<String, dynamic> studentData;

  const DashboardPage({super.key, required this.studentData});

  @override
  Widget build(BuildContext context) {
    // Mengambil data dari JSON response backend
    final String name = studentData['nama'] ?? 'Student';
    final String nim = studentData['nim'] ?? '';
    final List courses = studentData['courses'] ?? [];

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0b1a58),
        foregroundColor: Colors.white,
        title: const Text("Student Dashboard"),
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Kartu Profil
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: const [BoxShadow(color: Color(0x0D000000), blurRadius: 10, offset: Offset(0, 5))],
                border: const Border(left: BorderSide(color: Color(0xFF3b82f6), width: 5)),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundColor: const Color(0xFFE0F2FE),
                    child: Text(name[0], style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF0369A1))),
                  ),
                  const SizedBox(width: 15),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("Welcome back,", style: TextStyle(color: Colors.grey[600], fontSize: 14)),
                        Text(name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                        Text("NIM: $nim", style: const TextStyle(color: Color(0xFF3b82f6), fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 30),

            // Daftar Mata Kuliah
            const Text("My Enrolled Courses", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
            const SizedBox(height: 15),
            
            Expanded(
              child: courses.isEmpty
                  ? const Center(child: Text("No courses found for this student."))
                  : ListView.builder(
                      itemCount: courses.length,
                      itemBuilder: (context, index) {
                        final course = courses[index];
                        return Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(15),
                            border: Border.all(color: const Color(0xFFE2E8F0)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.book, color: Color(0xFF94A3B8)),
                              const SizedBox(width: 15),
                              Text(
                                course['course_name'],
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Color(0xFF334155)),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),

            // Tombol Utama Scan Absensi
            SizedBox(
              width: double.infinity,
              height: 60,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => ScannerPage(studentNim: nim)),
                  );
                },
                icon: const Icon(Icons.qr_code_scanner, color: Colors.white),
                label: const Text(
                  "SCAN FOR ATTENDANCE",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF10B981), // Emerald Green
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  elevation: 5,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

//////////////////////////////////////////////////
// 📷 3. SCANNER PAGE
//////////////////////////////////////////////////

class ScannerPage extends StatefulWidget {
  final String studentNim;

  const ScannerPage({super.key, required this.studentNim});

  @override
  State<ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<ScannerPage> {
  String scannedData = "Awaiting QR Code...";
  bool isScanned = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0b1a58),
        foregroundColor: Colors.white,
        title: const Text("Scan QR Code", style: TextStyle(fontWeight: FontWeight.bold)),
        elevation: 0,
      ),
      body: Column(
        children: [
          Expanded(
            flex: 5,
            child: Container(
              margin: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 15, offset: const Offset(0, 5))],
                border: Border.all(color: const Color(0xFFE2E8F0), width: 2),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(22),
                child: MobileScanner(
                  onDetect: (barcodeCapture) {
                    if (isScanned) return;
                    final barcode = barcodeCapture.barcodes.first;
                    final String? code = barcode.rawValue;

                    if (code != null) {
                      setState(() {
                        scannedData = code;
                        isScanned = true;
                      });
                    }
                  },
                ),
              ),
            ),
          ),
          Expanded(
            flex: 4,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 30),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: const BorderRadius.only(topLeft: Radius.circular(30), topRight: Radius.circular(30)),
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -5))],
              ),
              child: Column(
                children: [
                  Icon(isScanned ? Icons.check_circle : Icons.qr_code_scanner, size: 50, color: isScanned ? const Color(0xFF10B981) : const Color(0xFF94A3B8)),
                  const SizedBox(height: 10),
                  Text(isScanned ? "QR Code Detected!" : "Point camera at the lecturer's screen", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isScanned ? const Color(0xFF10B981) : const Color(0xFF334155))),
                  const SizedBox(height: 5),
                  Text(isScanned ? "Ready to submit attendance" : scannedData, style: const TextStyle(color: Color(0xFF64748B), fontSize: 13), textAlign: TextAlign.center),
                  const Spacer(),
                  SizedBox(
                    width: double.infinity,
                    height: 55,
                    child: ElevatedButton(
                      onPressed: isScanned
                          ? () async {
                              try {
                                final deviceId = await DeviceService.getDeviceId();
                                final url = Uri.parse("http://192.168.1.105:5001/api/attendance/scan");

                                final response = await http.post(
                                  url,
                                  headers: {"Content-Type": "application/json"},
                                  body: jsonEncode({"nim": widget.studentNim, "token_qr": scannedData, "device_id": deviceId}),
                                );

                                final result = jsonDecode(response.body);
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text(result["message"] ?? "No message"),
                                    backgroundColor: result["status"] == "success" ? Colors.green : Colors.red,
                                  ),
                                );
                                
                                if(result["status"] == "success") {
                                  Navigator.pop(context); // Kembali ke dashboard jika sukses
                                }
                              } catch (e) {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Connection error"), backgroundColor: Colors.red));
                              }
                            }
                          : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF10B981),
                        disabledBackgroundColor: const Color(0xFFE2E8F0),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                        elevation: isScanned ? 5 : 0,
                      ),
                      child: Text("SUBMIT ATTENDANCE", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: isScanned ? Colors.white : const Color(0xFF94A3B8), letterSpacing: 1.2)),
                    ),
                  ),
                  const SizedBox(height: 10),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}