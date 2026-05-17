enum MealType { breakfast, lunch, dinner, snack }

class MealModel {
  final String name;
  final String imageUrl;
  final int calories;
  final double protein;
  final double carbs;
  final double fat;
  final MealType type;

  MealModel({
    required this.name,
    required this.imageUrl,
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.type,
  });
}