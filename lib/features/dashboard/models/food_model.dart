class FoodModel {
  final int? id;
  final String name;
  final int calories;
  final double protein;
  final double carbs;
  final double fat;
  final String mealType;
  final String? imageUrl;
  final String instructions;
  final String emoji;
  final String colorHex;

  FoodModel({
    this.id,
    required this.name,
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.mealType,
    this.imageUrl,
    required this.instructions,
    this.emoji = '🍽️',
    this.colorHex = '#F2F2F2',
  });

  factory FoodModel.fromJson(Map<String, dynamic> json) {
    return FoodModel(
      id: json['id'] as int?,
      name: json['name'] ?? json['recipe_name'] ?? json['recipe'] ?? json['title'] ?? 'Unknown Meal',
      calories: _toInt(json['calories'] ?? json['calories_estimate'] ?? 0),
      protein: _toDouble(json['protein']),
      carbs: _toDouble(json['carbs']),
      fat: _toDouble(json['fat']),
      mealType: json['meal_type'] ?? json['type'] ?? '',
      imageUrl: json['image_url'] ?? json['image'] ?? '',
      instructions: json['instructions'] ?? json['description'] ?? 'No steps available.',
      emoji: json['emoji'] ?? '🍽️',
      colorHex: json['color_hex'] ?? '#F2F2F2',
    );
  }

  // دوال مساعدة لمنع حدوث الـ Errors عند تحويل أنواع البيانات
  static double _toDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is int) return value.toDouble();
    if (value is double) return value;
    if (value is String) return double.tryParse(value) ?? 0.0;
    return 0.0;
  }

  static int _toInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }

  Map<String, dynamic> toJson() {
    return {
      "id": id,
      "name": name,
      "calories": calories,
      "protein": protein,
      "carbs": carbs,
      "fat": fat,
      "meal_type": mealType,
      "image_url": imageUrl,
      "instructions": instructions,
    };
  }
}