import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../dashboard/models/food_model.dart'; // تأكد من استيراد الموديل الصحيح
import '../../../config/api_config.dart';

class MealService {
  // افترض أن هذا هو رابط الـ API الخاص بك
  // added api for features of 4-5 + also changed on line 12
  final String baseUrl = "${ApiConfig.baseUrl}/api"; 

      Future<List<FoodModel>> getMeals(String accessToken) async {
    final response = await http.get(
      Uri.parse('$baseUrl/meals/saved/'),
      headers: {
        'Authorization': 'Bearer $accessToken',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      List<dynamic> body = json.decode(response.body);

      List<FoodModel> meals = body.map((dynamic item) {
        return FoodModel(
          id: item['id'] as int?,
          name: item['recipe_name'] ?? '',
          calories: (item['calories'] ?? 0).toInt(),
          protein: (item['protein'] ?? 0).toDouble(),
          carbs: (item['carbs'] ?? 0).toDouble(),
          fat: (item['fat'] ?? 0).toDouble(),
          mealType: 'saved',
          imageUrl: item['image_url'] ?? '',
          instructions: item['instructions'] ?? '',
        );
      }).toList();

      return meals;
    } else {
      throw Exception("Failed to load meals");
    }
  }
}