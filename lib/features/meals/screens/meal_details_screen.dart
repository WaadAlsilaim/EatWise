import 'package:flutter/material.dart';
import '../../dashboard/models/food_model.dart'; 
import 'dart:convert';
import 'package:http/http.dart' as http;

class MealDetailsScreen extends StatelessWidget {
  final FoodModel meal;
  final String accessToken;

  const MealDetailsScreen({
    super.key,
    required this.meal,
    required this.accessToken,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: const BackButton(color: Colors.black),
        title: const Text("Meal Details", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              meal.name, 
              style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold)
            ),
            const SizedBox(height: 10),
            _infoChip("🔥 ${meal.calories.toInt()} kcal"),
            
            const Divider(height: 40, thickness: 1),
            
            _sectionTitle("Macros Breakdown"),
            // استخدام الألوان الجديدة المعتمدة
            _macroBar("Protein", meal.protein.toDouble(), const Color(0xFF90C2A9)), 
            _macroBar("Carbs", meal.carbs.toDouble(), const Color(0xFFFBD49B)),   
            _macroBar("Fats", meal.fat.toDouble(), const Color(0xFF9CEBFE)),     
            
            const Divider(height: 40, thickness: 1),
            
            _sectionTitle("Preparation Steps"),
            Container(
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(
                color: const Color(0xFFF3F6F4), 
                borderRadius: BorderRadius.circular(15),
              ),
              child: Text(
                meal.instructions.isNotEmpty
                    ? meal.instructions
                    : "No preparation steps available.",
                style: const TextStyle(fontSize: 16, height: 1.5, color: Colors.black87),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
      // تم حذف الـ bottomNavigationBar بالكامل من هنا
    );
  }

  Widget _sectionTitle(String title) => Padding(
        padding: const EdgeInsets.only(bottom: 15), 
        child: Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold))
      );
  
  Widget _macroBar(String label, double value, Color color) => Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween, 
            children: [
              Text(label, style: const TextStyle(fontWeight: FontWeight.w500)), 
              Text("${value.toStringAsFixed(1)}g", style: TextStyle(color: color, fontWeight: FontWeight.bold))
            ]
          ), 
          const SizedBox(height: 8), 
          LinearProgressIndicator(
            value: (value / 100).clamp(0.0, 1.0), 
            color: color, 
            backgroundColor: color.withOpacity(0.1), 
            minHeight: 8,
            borderRadius: BorderRadius.circular(10),
          ), 
          const SizedBox(height: 15)
        ]
      );

  Widget _infoChip(String text) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8), 
        decoration: BoxDecoration(
          color: const Color(0xFF90C2A9).withOpacity(0.15), 
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: const Color(0xFF90C2A9).withOpacity(0.3))
        ), 
        child: Text(
          text, 
          style: const TextStyle(color: Color(0xFF5A8B73), fontWeight: FontWeight.bold)
        )
      );
}