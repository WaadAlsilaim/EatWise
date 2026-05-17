import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../dashboard/models/food_model.dart';
import '../../../widgets/food_image.dart';
import 'meal_details_screen.dart';
import '../../../config/api_config.dart';

class MealsScreen extends StatefulWidget {
  final String accessToken;
  const MealsScreen({super.key, required this.accessToken});

  @override
  State<MealsScreen> createState() => _MealsScreenState();
}

class _MealsScreenState extends State<MealsScreen> {
  List<FoodModel> savedMeals = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchSavedRecipes();
  }

  // جلب الوصفات المحفوظة من السيرفر
  Future<void> _fetchSavedRecipes() async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConfig.baseUrl}/api/meals/saved/"),
        headers: {
          "Authorization": "Bearer ${widget.accessToken}",
          "Content-Type": "application/json",
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          savedMeals = data.map((json) => FoodModel.fromJson(json)).toList();
          isLoading = false;
        });
      } else {
        setState(() => isLoading = false);
      }
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  // دالة الحذف (Unsave) وإزالة الوجبة من القائمة
  Future<void> _deleteRecipe(int? mealId, int index) async {
    if (mealId == null) return;

    final removedMeal = savedMeals[index];
    setState(() {
      savedMeals.removeAt(index);
    });

    try {
      final response = await http.delete(
        Uri.parse("${ApiConfig.baseUrl}/api/meals/delete/$mealId/"),
        headers: {
          "Authorization": "Bearer ${widget.accessToken}",
          "Content-Type": "application/json",
        },
      );

      if (response.statusCode == 204 || response.statusCode == 200) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Recipe removed from My Meals ✅"),
            backgroundColor: Colors.redAccent,
            behavior: SnackBarBehavior.floating,
            duration: Duration(seconds: 2),
          ),
        );
      } else {
        // إعادة الوجبة إذا فشل الحذف في السيرفر
        setState(() => savedMeals.insert(index, removedMeal));
      }
    } catch (e) {
      setState(() => savedMeals.insert(index, removedMeal));
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
        title: const Text("Saved Recipes", 
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 18)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Colors.black, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF4CAF50)))
          : savedMeals.isEmpty
              ? _buildEmptyState()
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                  itemCount: savedMeals.length,
                  itemBuilder: (context, index) => _buildModernRecipeCard(savedMeals[index], index),
                ),
    );
  }

  Widget _buildModernRecipeCard(FoodModel food, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 15, offset: const Offset(0, 8)),
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
                  emoji: food.emoji,
                  colorHex: food.colorHex,
                  imageUrl: food.imageUrl,
                  size: 56,
                  borderRadius: 16,
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    food.name,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
                // أيقونة الحذف
                GestureDetector(
                  onTap: () => _deleteRecipe(food.id, index),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.bookmark_remove_outlined,
                      color: Color(0xFF4CAF50),
                      size: 22,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            
            // الماكروز بالتنسيق العمودي المطلوب
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildMacroInfo("${food.calories.toInt()}", "kcal", const Color(0xFF4CAF50)),
                _buildMacroInfo("${food.protein.toInt()}g", "Protein", const Color(0xFF90C2A9)),
                _buildMacroInfo("${food.carbs.toInt()}g", "Carbs", const Color(0xFFFBD49B)),
                _buildMacroInfo("${food.fat.toInt()}g", "Fat", const Color(0xFF9CEBFE)),
              ],
            ),
            
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 18),
              child: Divider(height: 1, color: Color(0xFFEEEEEE)),
            ),
            
            // زر عرض التفاصيل
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => MealDetailsScreen(meal: food, accessToken: widget.accessToken),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFF3F6F4),
                  foregroundColor: const Color(0xFF4CAF50),
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: const Text("View Full Details", style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // دالة عرض الماكروز (القيمة فوق التسمية)
  Widget _buildMacroInfo(String value, String label, Color color) {
    return Column(
      children: [
        Text(
          value, 
          style: TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: color)
        ),
        const SizedBox(height: 4),
        Text(
          label, 
          style: const TextStyle(color: Colors.grey, fontSize: 11, fontWeight: FontWeight.w600)
        ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.bookmark_border, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 15),
          const Text("No saved recipes yet", 
            style: TextStyle(color: Colors.grey, fontWeight: FontWeight.bold, fontSize: 16)),
        ],
      ),
    );
  }
}