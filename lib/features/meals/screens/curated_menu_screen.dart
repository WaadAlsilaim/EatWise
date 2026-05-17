import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'meal_details_screen.dart';
import '../../dashboard/models/food_model.dart';
import '../../../widgets/food_image.dart';
import '../../../config/api_config.dart';

class CuratedMenuScreen extends StatefulWidget {
  final List<int> selectedProductIds;
  final String accessToken;

  const CuratedMenuScreen({
    super.key,
    required this.selectedProductIds,
    required this.accessToken,
  });

  @override
  State<CuratedMenuScreen> createState() => _CuratedMenuScreenState();
}

class _CuratedMenuScreenState extends State<CuratedMenuScreen> {
  List<dynamic> suggestedMeals = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRecipes();
  }

  Future<void> _loadRecipes() async {
    final String baseUrl = "${ApiConfig.baseUrl}";
    final String ids = widget.selectedProductIds.join(',');

    try {
      final response = await http.get(
        Uri.parse("$baseUrl/api/meals/recommendations/?ids=$ids"),
        headers: {
          "Authorization": "Bearer ${widget.accessToken}",
          "Content-Type": "application/json",
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          suggestedMeals = data["recommended_recipes"] ?? [];
          isLoading = false;
        });
      } else {
        setState(() => isLoading = false);
      }
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  Future<void> _saveRecipeToMyMeals(dynamic meal) async {
    final String baseUrl = "${ApiConfig.baseUrl}";
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/api/meals/save/"),
        headers: {
          "Authorization": "Bearer ${widget.accessToken}",
          "Content-Type": "application/json",
        },
        body: jsonEncode({
          "recipe_name": meal['recipe'] ?? meal['name'],
          "calories": meal['calories_estimate'] ?? meal['calories'],
          "protein": meal['protein'],
          "carbs": meal['carbs'],
          "fat": meal['fat'],
          "image_url": meal['image'] ?? "",
          "instructions":
              meal['instructions'] ?? "Check details for full instructions",
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Recipe added to My Meals! ✅"),
            backgroundColor: Color(0xFF4CAF50),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      debugPrint("Save error: $e");
    }
  }

  double _parseToDouble(dynamic value) {
    if (value == null) return 0;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString()) ?? 0;
  }

  Map<String, String> _getActivitySuggestion(dynamic meal) {
    final double calories =
        _parseToDouble(meal['calories_estimate'] ?? meal['calories']);

    if (calories >= 800) {
      return {
        "title": "Activity Suggestion",
        "suggestion":
            "Try a 20–30 minute walk or a short workout session."
      };
    } else if (calories >= 600) {
      return {
        "title": "Activity Suggestion",
        "suggestion":
            "A 15–25 minute walk or light exercise would be a great choice."
      };
    } else if (calories >= 400) {
      return {
        "title": "Activity Suggestion",
        "suggestion":
            "Consider a 10–20 minute walk or some stretching."
      };
    } else {
      return {
        "title": "Activity Suggestion",
        "suggestion":
            "A short walk or gentle movement would be enough."
      };
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0.5,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Colors.black, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          "EatWise Suggestions",
          style: TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
      ),
      body: isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF4CAF50)),
            )
          : suggestedMeals.isEmpty
              ? const Center(child: Text("No recipes found for these items."))
              : ListView.builder(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                  itemCount: suggestedMeals.length,
                  itemBuilder: (context, index) =>
                      _buildModernMealCard(suggestedMeals[index]),
                ),
    );
  }

  Widget _buildModernMealCard(dynamic meal) {
    final activity = _getActivitySuggestion(meal);

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                FoodImage(
                  emoji: meal['emoji'] ?? '🍽️',
                  colorHex: meal['color_hex'] ?? '#F2F2F2',
                  imageUrl: meal['image_url'] ?? meal['image'] ?? '',
                  size: 56,
                  borderRadius: 16,
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        meal['recipe'] ?? meal['name'] ?? 'Healthy Meal',
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if ((meal['title_ar'] ?? '').toString().isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: Text(
                            meal['title_ar'],
                            style: const TextStyle(
                              fontSize: 13,
                              color: Colors.grey,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                GestureDetector(
                  onTap: () => _saveRecipeToMyMeals(meal),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.bookmark_add_outlined,
                      color: Color(0xFF4CAF50),
                      size: 22,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildMacroInfo(
                  "${meal['calories_estimate'] ?? meal['calories']}",
                  "kcal",
                  const Color(0xFF4CAF50),
                ),
                _buildMacroInfo(
                  "${meal['protein']}g",
                  "Protein",
                  const Color(0xFF90C2A9),
                ),
                _buildMacroInfo(
                  "${meal['carbs']}g",
                  "Carbs",
                  const Color(0xFFFBD49B),
                ),
                _buildMacroInfo(
                  "${meal['fat']}g",
                  "Fat",
                  const Color(0xFF9CEBFE),
                ),
              ],
            ),
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 18),
              child: Divider(height: 1, color: Color(0xFFEEEEEE)),
            ),
            Text(
              "Custom recipe based on your pantry. Balanced and ready in no time.",
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 13,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFFF6FBF7),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFDDEFE1)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.directions_walk_rounded,
                    color: Color(0xFF4CAF50),
                    size: 22,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          activity["title"]!,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                            color: Color(0xFF2E7D32),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          activity["suggestion"]!,
                          style: TextStyle(
                            color: Colors.grey[700],
                            fontSize: 12,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  final food = FoodModel.fromJson(meal);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => MealDetailsScreen(
                        meal: food,
                        accessToken: widget.accessToken,
                      ),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFF3F6F4),
                  foregroundColor: const Color(0xFF4CAF50),
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(15),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: const Text(
                  "View Full Details",
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMacroInfo(String value, String label, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.w900,
            fontSize: 15,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            color: Colors.grey,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
