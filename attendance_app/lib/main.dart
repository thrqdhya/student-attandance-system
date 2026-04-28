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
    return const MaterialApp(
      home: LoginPage(),
    );
  }
}

//////////////////////////////////////////////////
// LOGIN PAGE
//////////////////////////////////////////////////

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final TextEditingController nimController = TextEditingController();

  void login() {
    String nim = nimController.text;

    if (nim.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please enter NIM")),
      );
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ScannerPage(studentNim: nim),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Login")),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              "Enter your NIM",
              style: TextStyle(fontSize: 18),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: nimController,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: "NIM",
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: login,
              child: const Text("LOGIN"),
            ),
          ],
        ),
      ),
    );
  }
}

//////////////////////////////////////////////////
// SCANNER PAGE
//////////////////////////////////////////////////

class ScannerPage extends StatefulWidget {
  final String studentNim;

  const ScannerPage({super.key, required this.studentNim});

  @override
  State<ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<ScannerPage> {
  String scannedData = "Scan QR for attendance";
  bool isScanned = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("QR Scanner")),
      body: Column(
        children: [
          Expanded(
            flex: 4,
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

                  print("QR RESULT: $code");
                }
              },
            ),
          ),

          Expanded(
            flex: 2,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  "NIM: ${widget.studentNim}",
                  style: const TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 10),

                Text(
                  scannedData,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),

                if (isScanned)
                  ElevatedButton(
                    onPressed: () async {
                      final url = Uri.parse(
                          "http://192.168.1.111:5001/api/attendance/scan"); // GANTI IP

                      final response = await http.post(
                        url,
                        headers: {"Content-Type": "application/json"},
                        body: jsonEncode({
                          "nim": widget.studentNim,
                          "token_qr": scannedData
                        }),
                      );

                      final result = jsonDecode(response.body);

                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(result["message"] ?? "No message"),
                          backgroundColor: result["status"] == "success"
                              ? Colors.green
                              : Colors.red,
                        ),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 40, vertical: 15),
                    ),
                    child: const Text(
                      "PRESENT",
                      style: TextStyle(fontSize: 18, color: Colors.white),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}