import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class ApiService {
  // 🔗 BACKEND BASE URL
  static String get baseUrl => ApiConfig.baseUrl;
  // If Android emulator → 127.0.0.1
  // If real phone → your PC IP (e.g. 192.168.1.5)

  /// 📩 SEND OTP
  static Future<bool> sendOtp(String phone) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/send-otp/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'phone_number': phone}),
    );

    return response.statusCode == 200;
  }

  /// ✅ VERIFY OTP
  static Future<bool> verifyOtp(String phone, String code) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/verify-otp/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'phone_number': phone,
        'otp': code,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('accessToken', data['access']);
      return true;
    }
    return false;
  }
}