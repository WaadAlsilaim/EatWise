import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../products/screens/products_screen.dart';
import '../../../config/api_config.dart';

/// Shows the REAL AI analysis result returned by POST /analyze-image
class ImageResultScreen extends StatelessWidget {
  final Map<String, dynamic> result;
  final String imagePath;
  final String accessToken;

  const ImageResultScreen({
    super.key,
    required this.result,
    required this.imagePath,
    required this.accessToken,
  });

  @override
  Widget build(BuildContext context) {
    final name = result['name'] ?? result['recipe_name'] ?? 'Meal';
    final kcal = (result['calories'] ?? 0) as num;
    final protein = (result['protein'] ?? 0) as num;
    final carbs = (result['carbs'] ?? 0) as num;
    final fat = (result['fat'] ?? 0) as num;
    final List detected = (result['detected_items'] as List?) ?? [];
    final List warnings = (result['allergy_warnings'] as List?) ?? [];
    final String status = (result['ai_status'] ?? '').toString();
    final int pantryAdded = (result['pantry_added_count'] ?? 0) as int;
    final int pantryTotal = (result['pantry_total_detected'] ?? detected.length) as int;

    // Hide the calories/macros block whenever the AI didn't actually detect
    // anything — otherwise we'd be showing fake "0 kcal / 0 g" tiles that
    // look like a real result but mean nothing.
    final bool hasRealDetection =
        status == "ok" && detected.isNotEmpty;

    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0.5,
        title: const Text("Analysis Result",
            style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Colors.black, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image preview
            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: Image.file(File(imagePath),
                  height: 220, width: double.infinity, fit: BoxFit.cover),
            ),
            const SizedBox(height: 16),

            // Pantry confirmation banner
            if (pantryTotal > 0) _buildPantryBanner(context, pantryAdded, pantryTotal),

            const SizedBox(height: 6),

            // Status chip + raw class hints (debug-helpful)
            if (status == "no_detections" || status == "unavailable") ...[
              _buildInfoChip(
                icon: Icons.info_outline,
                color: const Color(0xFFFFF8E1),
                textColor: const Color(0xFF8C6A00),
                text: status == "unavailable"
                    ? "AI engine not installed — showing a suggestion based on your profile."
                    : "Nothing matched our food catalog. Try a closer, well-lit photo, or add the items manually from My Products → +",
              ),
              if (((result['raw_classes'] as List?) ?? []).isNotEmpty)
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.only(bottom: 14),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEEEEEE),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("AI saw (but didn't match a food in our DB):",
                          style: TextStyle(
                              color: Colors.grey,
                              fontWeight: FontWeight.bold,
                              fontSize: 11)),
                      const SizedBox(height: 4),
                      Wrap(
                        spacing: 6, runSpacing: 4,
                        children: ((result['raw_classes'] as List?) ?? [])
                            .toSet()
                            .map<Widget>((c) => Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(c.toString(),
                                      style: const TextStyle(fontSize: 11)),
                                ))
                            .toList(),
                      ),
                    ],
                  ),
                ),
            ],

            // Title + kcal — only when we actually have a detection
            Text(name,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            if (hasRealDetection) ...[
              Text("${kcal.toInt()} kcal (estimated)",
                  style: const TextStyle(fontSize: 18, color: Color(0xFF4CAF50))),
              const SizedBox(height: 24),

              // Macros block (hidden when no detection so we don't show 0/0/0)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _macroItem("Protein", "${protein.toStringAsFixed(1)}g",
                        const Color(0xFF90C2A9)),
                    _macroItem("Carbs", "${carbs.toStringAsFixed(1)}g",
                        const Color(0xFFFBD49B)),
                    _macroItem("Fat", "${fat.toStringAsFixed(1)}g",
                        const Color(0xFF9CEBFE)),
                  ],
                ),
              ),
            ] else ...[
              const SizedBox(height: 12),
              const Text(
                "We couldn't recognize any food in this photo.\n"
                "Try a closer, well-lit shot of a single item, "
                "or add it manually from My Products → +.",
                style: TextStyle(color: Colors.grey, fontSize: 13, height: 1.5),
              ),
            ],

            // Allergy warnings
            if (warnings.isNotEmpty) ...[
              const SizedBox(height: 16),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFEBEE),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("Allergy warnings",
                        style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Color(0xFFC62828))),
                    const SizedBox(height: 6),
                    ...warnings.map((w) => Text(w.toString(),
                        style: const TextStyle(color: Color(0xFFC62828)))),
                  ],
                ),
              ),
            ],

            // Detected items list
            if (detected.isNotEmpty) ...[
              const SizedBox(height: 20),
              const Text("Detected items",
                  style:
                      TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              ...detected.map((it) => _buildDetectedItem(it)),
            ],

            const SizedBox(height: 24),

            // PRIMARY action: Save the detected ingredients to My Products
            // (already saved server-side; this is the explicit confirmation
            // + navigation so the user can immediately get suggestions).
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _saveToMyProducts(context, pantryAdded, pantryTotal),
                icon: const Icon(Icons.add_shopping_cart, color: Colors.white),
                label: Text(
                  pantryAdded > 0
                      ? "Save to My Products  →  Get Suggestions"
                      : "Open My Products  →  Get Suggestions",
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 15),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4CAF50),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
              ),
            ),

            const SizedBox(height: 10),

            // SECONDARY action: Save the whole detected meal as a saved recipe
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => _saveMeal(context),
                icon: const Icon(Icons.bookmark_add_outlined,
                    color: Color(0xFF4CAF50)),
                label: const Text("Save as Meal",
                    style: TextStyle(
                        color: Color(0xFF4CAF50),
                        fontWeight: FontWeight.bold)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(
                      color: Color(0xFF4CAF50), width: 1.5),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
              ),
            ),
            const SizedBox(height: 14),
            // Required by SFDA General Wellness classification
            const Text(
              "Not intended for medical purposes. For general wellness only.\n"
              "غير مخصص للأغراض الطبية — للعافية العامة فقط.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetectedItem(dynamic it) {
    final label = it['food_name_en'] ?? it['label'] ?? '';
    final ar = it['food_name_ar'] ?? '';
    final conf = (it['confidence'] ?? 0) as num;
    final bool lowConf = (it['low_confidence'] == true) || conf < 0.5;
    final nut = (it['nutrition'] as Map?) ?? {};
    final kcal = (nut['kcal'] ?? 0) as num;

    // Color the confidence pill by certainty level
    final Color confColor = conf >= 0.7
        ? const Color(0xFF4CAF50)         // green: high
        : conf >= 0.5
            ? const Color(0xFFFF9800)     // orange: medium
            : const Color(0xFFE53935);    // red: low

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: lowConf
            ? Border.all(color: const Color(0xFFFFB74D), width: 1)
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                lowConf ? Icons.help_outline : Icons.check_circle,
                color: confColor,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label,
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 15)),
                    if (ar.isNotEmpty)
                      Text(ar,
                          style: const TextStyle(
                              color: Colors.grey, fontSize: 13)),
                    Text("${kcal.toStringAsFixed(0)} kcal / 100g",
                        style:
                            const TextStyle(color: Colors.grey, fontSize: 12)),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: confColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text("${(conf * 100).toInt()}%",
                    style: TextStyle(
                        color: confColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 12)),
              ),
            ],
          ),
          if (lowConf) ...[
            const SizedBox(height: 8),
            Row(
              children: const [
                Icon(Icons.info_outline,
                    size: 14, color: Color(0xFFE65100)),
                SizedBox(width: 6),
                Expanded(
                  child: Text(
                    "Low confidence — please verify or edit from My Products.",
                    style: TextStyle(
                        color: Color(0xFFE65100), fontSize: 11),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildInfoChip({
    required IconData icon,
    required Color color,
    required Color textColor,
    required String text,
  }) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(icon, color: textColor, size: 18),
          const SizedBox(width: 8),
          Expanded(
              child: Text(text,
                  style: TextStyle(color: textColor, fontSize: 13))),
        ],
      ),
    );
  }

  /// Banner shown when the analysis pushed items into the user's pantry.
  Widget _buildPantryBanner(BuildContext context, int added, int total) {
    final msg = added > 0
        ? "$added new item${added == 1 ? "" : "s"} added to your pantry"
        : "All $total detected item${total == 1 ? "" : "s"} are already in your pantry";
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(14, 12, 12, 12),
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F5E9),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF4CAF50).withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.check_circle_outline,
              color: Color(0xFF4CAF50), size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(msg,
                    style: const TextStyle(
                        color: Color(0xFF2E7D32),
                        fontWeight: FontWeight.bold,
                        fontSize: 13)),
                const SizedBox(height: 2),
                const Text(
                  "Tap the green button below to view them and get recipe suggestions.",
                  style: TextStyle(
                      color: Color(0xFF558B2F), fontSize: 11),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _macroItem(String label, String value, Color color) => Column(
        children: [
          Text(value,
              style: TextStyle(
                  fontWeight: FontWeight.w900, fontSize: 18, color: color)),
          const SizedBox(height: 4),
          Text(label,
              style: const TextStyle(
                  color: Colors.grey,
                  fontSize: 12,
                  fontWeight: FontWeight.w600)),
        ],
      );

  /// Confirms that detected ingredients are in My Products, then navigates.
  ///
  /// The backend already auto-adds detected items to the user's pantry during
  /// /analyze-image. This method makes that fact visible to the user and
  /// takes them directly to My Products, where they can tap "Get Suggestions"
  /// to receive recipe recommendations based on what they have.
  void _saveToMyProducts(BuildContext context, int added, int total) {
    final msg = added > 0
        ? "✅ Saved $added ingredient${added == 1 ? "" : "s"} to My Products"
        : total > 0
            ? "All $total ingredient${total == 1 ? "" : "s"} are already in My Products"
            : "Opening My Products…";
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: const Color(0xFF4CAF50),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => ProductsScreen(accessToken: accessToken),
      ),
    );
  }

  Future<void> _saveMeal(BuildContext context) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConfig.baseUrl}/api/meals/save/"),
        headers: {
          "Authorization": "Bearer $accessToken",
          "Content-Type": "application/json",
        },
        body: jsonEncode({
          "recipe_name": result['name'] ?? 'Detected Meal',
          "calories": result['calories'] ?? 0,
          "protein": result['protein'] ?? 0,
          "carbs": result['carbs'] ?? 0,
          "fat": result['fat'] ?? 0,
          "image_url": result['image_url'] ?? "",
          "instructions": result['instructions'] ?? "",
        }),
      );
      if (!context.mounted) return;
      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Saved to My Meals ✅"),
            backgroundColor: Color(0xFF4CAF50),
            behavior: SnackBarBehavior.floating,
          ),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text("Save failed (${response.statusCode})"),
              backgroundColor: Colors.red),
        );
      }
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text("Network error: $e"),
            backgroundColor: Colors.red),
      );
    }
  }
}
