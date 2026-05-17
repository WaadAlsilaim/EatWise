import 'package:flutter/material.dart';

class EatWiseOptionsSheet extends StatelessWidget {
  // دالتان فارغتان للتعامل مع نقرات المستخدم
  final VoidCallback onScanTap;
  final VoidCallback onUploadTap;

  const EatWiseOptionsSheet({
    super.key,
    required this.onScanTap,
    required this.onUploadTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      // تحديد شكل وحواف الصندوق السفلي
      decoration: const BoxDecoration(
        color: Color(0xFFF7F7F7), // لون خلفية الصندوق
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(24), // حواف دائرية من الأعلى
          topRight: Radius.circular(24),
        ),
      ),
      // المسافات الداخلية حول المحتوى كله
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Column(
        mainAxisSize: MainAxisSize.min, // لجعل الصندوق يأخذ حجم محتواه فقط
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // رأس الصندوق: شريط السحب وزر الإغلاق
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // شريط السحب الرمادي (مجرد زينة)
              const SizedBox(width: 48), // مسافة محاذاة فارغة
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300], // لون رمادي فاتح
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              // زر الإغلاق (X)
              IconButton(
                icon: const Icon(Icons.close, color: Colors.black, size: 20),
                onPressed: () => Navigator.pop(context), // إغلاق الصندوق
              ),
            ],
          ),
          const SizedBox(height: 16), // مسافة فارغة

          // النصوص الرئيسية
          const Center(
            child: Text(
              "Add to EatWise",
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.black,
              ),
            ),
          ),
          const SizedBox(height: 8), // مسافة فارغة
          Center(
            child: Text(
              "Select an option to start AI analysis",
              textAlign: TextAlign.center, // محاذاة النص في المنتصف
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600], // لون رمادي داكن قليلاً
              ),
            ),
          ),
          const SizedBox(height: 32), // مسافة فارغة قبل الخيارات

          // الخيار الأول: Scan Food / Product (الخيار الأخضر)
          GestureDetector(
            onTap: onScanTap, // دالة النقرة
            child: Container(
              padding: const EdgeInsets.all(16), // مسافات داخلية للزر
              decoration: BoxDecoration(
                color: const Color(0xFF4CAF50), // لون خلفية أخضر فاتح (من التصميم)
                borderRadius: BorderRadius.circular(16), // حواف دائرية للزر
              ),
              child: Row(
                children: [
                  // أيقونة المسح (نستخدم أيقونة مشابهة متوفرة)
                  const Icon(Icons.center_focus_weak, color: Colors.white, size: 32),
                  const SizedBox(width: 16), // مسافة بين الأيقونة والنص
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Scan Food / Product",
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600, // خط سميك متوسط
                          color: Colors.white, // نص أبيض للخلفية الملونة
                        ),
                      ),
                      const SizedBox(height: 4), // مسافة بين العنوان والنص الفرعي
                      Text(
                        "Use AI to identify items instantly",
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.white.withOpacity(0.9), // نص أبيض شفاف قليلاً
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16), // مسافة بين الخيارين

          // الخيار الثاني: Upload Image (الخيار الأبيض)
          GestureDetector(
            onTap: onUploadTap, // دالة النقرة
            child: Container(
              padding: const EdgeInsets.all(16), // مسافات داخلية للزر
              decoration: BoxDecoration(
                color: Colors.white, // لون خلفية أبيض
                borderRadius: BorderRadius.circular(16), // حواف دائرية للزر
              ),
              child: Row(
                children: [
                  // أيقونة معرض الصور (نستخدم أيقونة مشابهة)
                  const Icon(Icons.photo_library, color: Color(0xFF4CAF50), size: 32),
                  const SizedBox(width: 16), // مسافة بين الأيقونة والنص
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Upload Image",
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600, // خط سميك متوسط
                          color: Colors.black, // نص أسود للخلفية البيضاء
                        ),
                      ),
                      const SizedBox(height: 4), // مسافة بين العنوان والنص الفرعي
                      Text(
                        "Analyze meals from your gallery",
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600], // لون رمادي داكن قليلاً
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24), // مسافة فارغة في الأسفل
        ],
      ),
    );
  }
}