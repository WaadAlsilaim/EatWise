import 'dart:convert';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../profile/screens/profile_screen.dart';
import '../../../config/api_config.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController phoneController = TextEditingController();
  final TextEditingController otpController = TextEditingController();

  bool isLoading = false;
  bool isOtpSent = false;
  String? devCode; // shown only in development mode

  Future<void> sendOtp() async {
    final phone = phoneController.text.trim();
    if (phone.isEmpty) {
      showMessage("Please enter your phone number");
      return;
    }

    setState(() => isLoading = true);
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/api/accounts/send-otp/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'phone_number': phone}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          isOtpSent = true;
          // In dev mode (no SMS gateway), the backend returns the code
          // directly so we can display it for easy testing.
          devCode = data["dev_code"] as String?;
        });
        // Auto-fill the OTP field when running in dev mode
        if (devCode != null) {
          otpController.text = devCode!;
          showMessage("Dev OTP: $devCode (auto-filled)", color: Colors.green);
        } else {
          showMessage("OTP sent successfully", color: Colors.green);
        }
      } else {
        final data = jsonDecode(response.body);
        showMessage(data["error"] ?? "Error sending OTP");
      }
    } catch (e) {
      showMessage("Failed to connect to server");
    } finally {
      setState(() => isLoading = false);
    }
  }

  Future<void> verifyOtp() async {
    final code = otpController.text.trim();
    if (code.isEmpty) {
      showMessage("Please enter the OTP");
      return;
    }

    setState(() => isLoading = true);
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/api/accounts/verify-otp/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "phone_number": phoneController.text.trim(),
          "code": code,
        }),
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 200) {
        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => ProfileScreen(accessToken: data["access"]),
          ),
        );
      } else {
        showMessage(data["error"] ?? "Verification failed");
      }
    } catch (e) {
      showMessage("Server connection failed");
    } finally {
      setState(() => isLoading = false);
    }
  }

  void showMessage(String message, {Color color = Colors.red}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: color),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),
              const Text(
                "Verify Account",
                style: TextStyle(fontSize: 34, fontWeight: FontWeight.bold, color: Color(0xFF111827)),
              ),
              const SizedBox(height: 12),
              const Text(
                "We're verifying your device to keep your health data secure.",
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
              const SizedBox(height: 40),

              // 1. حقل رقم الجوال (يبقى ظاهراً دائماً)
              _buildLabel("PHONE NUMBER"),
              _buildTextField(
                controller: phoneController, 
                hint: "Enter phone number", 
                icon: Icons.phone_android,
                enabled: !isOtpSent, // يتم قفله بعد الإرسال لضمان عدم تغيير الرقم أثناء التحقق
              ),

              // 2. حقل الـ OTP (يظهر تحت الجوال فقط بعد الضغط على إرسال)
              if (isOtpSent) ...[
                const SizedBox(height: 25),
                _buildLabel("VERIFICATION CODE"),
                _buildTextField(
                  controller: otpController,
                  hint: "- - - - - -",
                  icon: Icons.lock_outline,
                  isOtp: true,
                ),
                // Dev-mode banner: show the OTP directly on screen so testing
                // doesn't require reading server logs.
                if (devCode != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF8E1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFFFE0A3)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.info_outline, color: Color(0xFFE6A100), size: 18),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            "Dev mode — OTP: $devCode",
                            style: const TextStyle(
                              color: Color(0xFF8C6A00),
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 15),
                Center(
                  child: TextButton(
                    onPressed: isLoading ? null : sendOtp,
                    child: const Text("Didn't receive it? Resend", style: TextStyle(color: Color(0xFF4CAF50))),
                  ),
                ),
              ],

              const SizedBox(height: 40),

              // 3. الزر (تتغير وظيفته بناءً على الحالة)
              SizedBox(
                width: double.infinity,
                height: 60,
                child: ElevatedButton(
                  onPressed: isLoading ? null : (isOtpSent ? verifyOtp : sendOtp),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF4CAF50),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  ),
                  child: isLoading 
                    ? const CircularProgressIndicator(color: Colors.white) 
                    : Text(
                        isOtpSent ? "Verify Account" : "Send OTP", 
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, left: 4),
      child: Text(text, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller, 
    required String hint, 
    required IconData icon, 
    bool isOtp = false,
    bool enabled = true,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: enabled ? Colors.white : Colors.grey[200],
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 5))],
      ),
      child: TextField(
        controller: controller,
        enabled: enabled,
        keyboardType: TextInputType.phone,
        textAlign: isOtp ? TextAlign.center : TextAlign.start,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        decoration: InputDecoration(
          hintText: hint,
          prefixIcon: isOtp ? null : Icon(icon, color: Colors.grey),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        ),
      ),
    );
  }
}

