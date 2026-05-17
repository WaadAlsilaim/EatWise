import 'package:flutter/material.dart';

class FeatureCard extends StatelessWidget {
  final String title;     // عنوان الكرت مثل "Products" أو "Meals"
  final IconData icon;    // أيقونة الكرت
  final Color iconColor;  // لون الأيقونة الرئيسي
  final VoidCallback? onTap; // 👈 أضفنا onTap اختياري

  const FeatureCard({
    super.key,
    required this.title,
    required this.icon,
    required this.iconColor,
    this.onTap, // 👈 اختياري
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap, // 👈 نربطه هنا
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white, // خلفية الكرت بيضاء
          borderRadius: BorderRadius.circular(15), // زوايا مستديرة
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.02), // ظل خفيف
              blurRadius: 10,
            )
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // أيقونة داخل مربع صغير
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: iconColor.withOpacity(0.1), // خلفية فاتحة من لون الأيقونة
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: iconColor, size: 28),
            ),
            const SizedBox(height: 12),
            // عنوان الكرت
            Text(
              title,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
      ),
    );
  }
}