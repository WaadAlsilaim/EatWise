// lib/features/services/food_service.dart
import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../dashboard/models/food_model.dart';

class FoodService {
  final String baseUrl;

  FoodService({required this.baseUrl});

  // تحليل صورة وإرجاع FoodModel من السيرفر
  Future<FoodModel> analyzeImage(File image) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/analyze-image'));
    request.files.add(await http.MultipartFile.fromPath('image', image.path));

    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return FoodModel.fromJson(data); // لازم السيرفر يرجع JSON مطابق لـ FoodModel
    } else {
      throw Exception('Failed to analyze image');
    }
  }

  // لاحقاً يمكن إضافة دوال أخرى مثل إضافة وجبة أو جلب وجبات اليوم
  Future<List<FoodModel>> getMeals(String userId) async {
    final response = await http.get(Uri.parse('$baseUrl/meals/$userId'));

    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body);
      return data.map((e) => FoodModel.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load meals');
    }
  }
}