import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../../widgets/food_image.dart';
import '../../../config/api_config.dart';

class AiRecipesScreen extends StatefulWidget {
  final String accessToken;
  const AiRecipesScreen({super.key, required this.accessToken});

  @override
  State<AiRecipesScreen> createState() => _AiRecipesScreenState();
}

class _AiRecipesScreenState extends State<AiRecipesScreen> {
  String get _base => ApiConfig.baseUrl;
  List<dynamic> allProducts = [];
  List<dynamic> recipes = [];
  bool isLoading = true;
  String _filter = "all";

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() => isLoading = true);
    try {
      // Fetch all products and generate recommendations using ALL their IDs
      final pr = await http.get(Uri.parse("$_base/api/products/products/?limit=50"));
      if (pr.statusCode == 200) {
        allProducts = jsonDecode(pr.body);
      }
      final ids = allProducts.map((p) => p["id"]).join(",");
      final r = await http.get(
        Uri.parse("$_base/api/meals/recommendations/?ids=$ids&limit=20"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body);
        recipes = (data["recommended_recipes"] as List?) ?? [];
      }
    } catch (_) {}
    if (mounted) setState(() => isLoading = false);
  }

  List<dynamic> get _filtered {
    if (_filter == "all") return recipes;
    if (_filter == "low") {
      return recipes.where((r) {
        final kcal = (r["calories"] ?? 0) as num;
        return kcal <= 400;
      }).toList();
    }
    if (_filter == "high") {
      return recipes.where((r) {
        final kcal = (r["calories"] ?? 0) as num;
        return kcal >= 600;
      }).toList();
    }
    // cuisine filter
    return recipes
        .where((r) => (r["cuisine"] ?? "").toString().toLowerCase() == _filter)
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildFilters(),
            Expanded(
              child: isLoading
                  ? const Center(
                      child: CircularProgressIndicator(color: Color(0xFF4CAF50)))
                  : _filtered.isEmpty
                      ? const Center(
                          child: Text("No recipes match this filter.",
                              style: TextStyle(color: Colors.grey)))
                      : RefreshIndicator(
                          onRefresh: _loadAll,
                          color: const Color(0xFF4CAF50),
                          child: ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _filtered.length,
                            itemBuilder: (_, i) => _recipeCard(_filtered[i]),
                          ),
                        ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                "AI Recipes",
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              const SizedBox(width: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFF4CAF50).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text("✨ smart",
                    style: TextStyle(
                        color: Color(0xFF4CAF50),
                        fontWeight: FontWeight.bold,
                        fontSize: 11)),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            "Personalized meals based on your profile and preferences",
            style: TextStyle(color: Colors.grey, fontSize: 13),
          ),
        ],
      ),
    );
  }

  Widget _buildFilters() {
    final filters = [
      {"key": "all", "label": "All"},
      {"key": "low", "label": "< 400 kcal"},
      {"key": "high", "label": "> 600 kcal"},
      {"key": "saudi", "label": "Saudi"},
      {"key": "levantine", "label": "Levantine"},
      {"key": "mediterranean", "label": "Mediterranean"},
      {"key": "italian", "label": "Italian"},
      {"key": "general", "label": "General"},
    ];
    return SizedBox(
      height: 48,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        itemCount: filters.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (_, i) {
          final f = filters[i];
          final active = _filter == f["key"];
          return GestureDetector(
            onTap: () => setState(() => _filter = f["key"]!),
            child: Container(
              alignment: Alignment.center,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: active ? const Color(0xFF4CAF50) : Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color:
                      active ? const Color(0xFF4CAF50) : Colors.grey.shade300,
                ),
              ),
              child: Text(
                f["label"]!,
                style: TextStyle(
                  color: active ? Colors.white : Colors.black87,
                  fontWeight: FontWeight.w600,
                  fontSize: 13,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _recipeCard(dynamic r) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.03),
              blurRadius: 10,
              offset: const Offset(0, 4)),
        ],
      ),
      child: Row(
        children: [
          FoodImage(
            emoji: r["emoji"] ?? "🍽️",
            colorHex: r["color_hex"] ?? "#F2F2F2",
            imageUrl: r["image_url"] ?? r["image"] ?? "",
            size: 72, borderRadius: 16,
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  r["name"] ?? r["recipe"] ?? "Recipe",
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 15),
                  maxLines: 1, overflow: TextOverflow.ellipsis,
                ),
                if ((r["title_ar"] ?? "").toString().isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(r["title_ar"],
                        style:
                            const TextStyle(color: Colors.grey, fontSize: 12)),
                  ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    _chip("${(r["calories"] ?? 0).toString()} kcal",
                        const Color(0xFF4CAF50)),
                    const SizedBox(width: 6),
                    if ((r["prep_time_min"] ?? 0) > 0)
                      _chip("${r["prep_time_min"]} min", Colors.grey),
                    const SizedBox(width: 6),
                    if ((r["cuisine"] ?? "").toString().isNotEmpty)
                      _chip(r["cuisine"], const Color(0xFF1E88E5)),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => _save(r),
            icon: const Icon(Icons.bookmark_add_outlined,
                color: Color(0xFF4CAF50)),
          ),
        ],
      ),
    );
  }

  Widget _chip(dynamic text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text.toString(),
        style: TextStyle(
            color: color, fontSize: 10, fontWeight: FontWeight.bold),
      ),
    );
  }

  Future<void> _save(dynamic r) async {
    try {
      final resp = await http.post(
        Uri.parse("$_base/api/meals/save/"),
        headers: {
          "Authorization": "Bearer ${widget.accessToken}",
          "Content-Type": "application/json",
        },
        body: jsonEncode({
          "recipe_name": r["name"] ?? r["recipe"],
          "calories": r["calories"] ?? 0,
          "protein": r["protein"] ?? 0,
          "carbs": r["carbs"] ?? 0,
          "fat": r["fat"] ?? 0,
          "image_url": r["image_url"] ?? "",
          "instructions": r["instructions"] ?? "",
        }),
      );
      if (!mounted) return;
      if (resp.statusCode == 201 || resp.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Saved to My Meals ✅"),
            backgroundColor: Color(0xFF4CAF50),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (_) {}
  }
}
