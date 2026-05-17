import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../../widgets/food_image.dart';
import '../../meals/screens/curated_menu_screen.dart';
import 'add_product_screen.dart';
import '../../../config/api_config.dart';

/// "My Products" — the user's pantry.
/// Items here are added either automatically by image analysis
/// or manually from the catalog. Pressing "Get Suggestions" sends the
/// pantry's food_ids to /api/meals/recommendations/.
class ProductsScreen extends StatefulWidget {
  final String accessToken;

  const ProductsScreen({super.key, required this.accessToken});

  @override
  State<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends State<ProductsScreen> {
  String get _base => ApiConfig.baseUrl;

  List<dynamic> items = [];
  Set<String> userAllergies = {};
  Set<int> selectedIds = {};        // selected food_ids for suggestions
  bool isLoading = true;

  bool get _allSelected =>
      items.isNotEmpty && selectedIds.length == items.length;

  void _toggleSelected(int foodId) {
    setState(() {
      if (selectedIds.contains(foodId)) {
        selectedIds.remove(foodId);
      } else {
        selectedIds.add(foodId);
      }
    });
  }

  void _selectAllOrNone() {
    setState(() {
      if (_allSelected) {
        selectedIds.clear();
      } else {
        selectedIds = items.map<int>((i) => i["food_id"] as int).toSet();
      }
    });
  }

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() => isLoading = true);
    await Future.wait([_loadPantry(), _loadAllergies()]);
    if (mounted) setState(() => isLoading = false);
  }

  Future<void> _loadPantry() async {
    try {
      final r = await http.get(
        Uri.parse("$_base/api/pantry/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (r.statusCode == 200) {
        items = jsonDecode(r.body);
        // By default, select every item so first-time users see "Get Suggestions (N)"
        // active immediately. They can deselect items they don't want to use.
        selectedIds = items.map<int>((i) => i["food_id"] as int).toSet();
      }
    } catch (_) {}
  }

  Future<void> _loadAllergies() async {
    try {
      final r = await http.get(
        Uri.parse("$_base/api/accounts/me/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body);
        final raw = (data["allergies"] ?? "").toString();
        if (raw.isNotEmpty && raw != "None") {
          userAllergies = raw
              .split(',')
              .map((s) => s.trim().toLowerCase())
              .where((s) => s.isNotEmpty)
              .toSet();
        }
      }
    } catch (_) {}
  }

  Future<void> _removeItem(int foodId) async {
    setState(() => items.removeWhere((i) => i["food_id"] == foodId));
    try {
      await http.delete(
        Uri.parse("$_base/api/pantry/$foodId/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
    } catch (_) {}
  }

  Future<void> _clearAll() async {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: const Text("Clear all products?"),
        content: const Text("Removes every item from your pantry."),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              try {
                await http.delete(
                  Uri.parse("$_base/api/pantry/"),
                  headers: {
                    "Authorization": "Bearer ${widget.accessToken}"
                  },
                );
              } catch (_) {}
              _loadPantry();
              setState(() {});
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
            child: const Text("Clear all"),
          ),
        ],
      ),
    );
  }

  void _openAddProduct() async {
    final added = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => AddProductScreen(accessToken: widget.accessToken),
      ),
    );
    if (added == true) _loadAll();
  }

  void _getSuggestions() {
    if (selectedIds.isEmpty) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CuratedMenuScreen(
          selectedProductIds: selectedIds.toList(),
          accessToken: widget.accessToken,
        ),
      ),
    );
  }

  bool _hasAllergyConflict(dynamic item) {
    if (userAllergies.isEmpty) return false;
    final name = (item["name"] ?? "").toString().toLowerCase();
    final cat = (item["category"] ?? "").toString().toLowerCase();
    final keywords = {
      "dairy": ["milk", "yogurt", "cheese", "laban", "dairy"],
      "peanuts": ["peanut"],
      "gluten": ["bread", "wheat", "flour", "pasta", "grain"],
      "shellfish": ["shrimp", "prawn", "crab", "lobster"],
      "soy": ["soy"], "eggs": ["egg"],
      "tree nuts": ["almond", "walnut", "nut"],
    };
    for (final a in userAllergies) {
      for (final entry in keywords.entries) {
        if (a.contains(entry.key)) {
          for (final kw in entry.value) {
            if (name.contains(kw) || cat.contains(kw)) return true;
          }
        }
      }
    }
    return false;
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
          "My Products",
          style: TextStyle(
              color: Colors.black, fontWeight: FontWeight.bold, fontSize: 18),
        ),
        actions: [
          if (items.isNotEmpty)
            IconButton(
              icon: Icon(
                _allSelected
                    ? Icons.check_box
                    : Icons.check_box_outline_blank,
                color: const Color(0xFF4CAF50),
              ),
              onPressed: _selectAllOrNone,
              tooltip: _allSelected ? "Deselect all" : "Select all",
            ),
          if (items.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined,
                  color: Colors.redAccent),
              onPressed: _clearAll,
              tooltip: "Clear all",
            ),
          IconButton(
            icon: const Icon(Icons.add, color: Color(0xFF4CAF50)),
            onPressed: _openAddProduct,
            tooltip: "Add product",
          ),
        ],
      ),
      body: isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF4CAF50)))
          : items.isEmpty
              ? _emptyState()
              : RefreshIndicator(
                  onRefresh: _loadAll,
                  color: const Color(0xFF4CAF50),
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
                    itemCount: items.length,
                    itemBuilder: (_, i) => _buildItemCard(items[i]),
                  ),
                ),
      bottomNavigationBar: items.isEmpty ? null : _suggestBar(),
    );
  }

  Widget _emptyState() {
    return ListView(
      padding: const EdgeInsets.all(40),
      children: [
        const SizedBox(height: 60),
        Icon(Icons.shopping_basket_outlined,
            size: 84, color: Colors.grey[300]),
        const SizedBox(height: 18),
        const Text("Your pantry is empty",
            textAlign: TextAlign.center,
            style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
                color: Colors.black87)),
        const SizedBox(height: 8),
        const Text(
          "Scan or upload a photo of your groceries from the home screen, "
          "or tap + to pick a product manually.",
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey, fontSize: 14, height: 1.5),
        ),
        const SizedBox(height: 24),
        ElevatedButton.icon(
          onPressed: _openAddProduct,
          icon: const Icon(Icons.add),
          label: const Text("Add a product"),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF4CAF50),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
      ],
    );
  }

  Widget _buildItemCard(dynamic item) {
    final hasAllergy = _hasAllergyConflict(item);
    final source = (item["source"] ?? "manual").toString();
    final foodId = item["food_id"] as int;
    final isSelected = selectedIds.contains(foodId);

    Color borderColor;
    if (hasAllergy) {
      borderColor = Colors.red[200]!;
    } else if (isSelected) {
      borderColor = const Color(0xFF4CAF50);
    } else {
      borderColor = Colors.transparent;
    }

    return Dismissible(
      key: ValueKey("p-$foodId"),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 24),
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.red[50], borderRadius: BorderRadius.circular(20),
        ),
        child: const Icon(Icons.delete_outline, color: Colors.red),
      ),
      onDismissed: (_) {
        selectedIds.remove(foodId);
        _removeItem(foodId);
      },
      child: GestureDetector(
        onTap: () => _toggleSelected(foodId),
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFFF1F8E9) : Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: borderColor, width: 2),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 10, offset: const Offset(0, 4),
              ),
            ],
        ),
          child: Row(
            children: [
              // Selection indicator (left)
              AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                width: 26, height: 26,
                margin: const EdgeInsets.only(right: 12),
                decoration: BoxDecoration(
                  color: isSelected
                      ? const Color(0xFF4CAF50)
                      : Colors.transparent,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: isSelected
                        ? const Color(0xFF4CAF50)
                        : Colors.grey.shade400,
                    width: 2,
                  ),
                ),
                child: isSelected
                    ? const Icon(Icons.check, color: Colors.white, size: 18)
                    : null,
              ),
              FoodImage(
                emoji: item["emoji"] ?? "🍽️",
                colorHex: item["color_hex"] ?? "#F2F2F2",
                imageUrl: item["image_url"] ?? "",
                size: 50, borderRadius: 14,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            item["name"] ?? "",
                            style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                                color: hasAllergy
                                    ? Colors.red[700]
                                    : Colors.black87),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (hasAllergy)
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: Colors.red[50],
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text("ALLERGY",
                                style: TextStyle(
                                    color: Colors.red[700],
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold)),
                          ),
                      ],
                    ),
                    if ((item["name_ar"] ?? "").toString().isNotEmpty)
                      Text(item["name_ar"],
                          style: const TextStyle(
                              color: Colors.grey, fontSize: 12)),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        _miniChip("${item["calories"] ?? 0} kcal",
                            const Color(0xFF4CAF50)),
                        const SizedBox(width: 6),
                        _miniChip(
                            source == "scan"
                                ? "📷 Scanned"
                                : source == "upload"
                                    ? "📸 Uploaded"
                                    : "✏️ Added",
                            Colors.grey),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _miniChip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(text,
          style: TextStyle(
              color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }

  Widget _suggestBar() {
    final hasSelection = selectedIds.isNotEmpty;
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 12, offset: const Offset(0, -4)),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Selection helper text
            if (hasSelection)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  "${selectedIds.length} of ${items.length} selected · tap items to toggle",
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
              )
            else
              const Padding(
                padding: EdgeInsets.only(bottom: 8),
                child: Text(
                  "Tap items above to choose what to suggest from",
                  style: TextStyle(color: Colors.grey, fontSize: 12),
                ),
              ),
            ElevatedButton.icon(
              onPressed: hasSelection ? _getSuggestions : null,
              icon: const Icon(Icons.auto_awesome),
              label: Text(
                hasSelection
                    ? "Get Suggestions (${selectedIds.length})"
                    : "Select at least 1 product",
                style: const TextStyle(
                    fontWeight: FontWeight.bold, fontSize: 16),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4CAF50),
                foregroundColor: Colors.white,
                disabledBackgroundColor: Colors.grey[300],
                disabledForegroundColor: Colors.grey[600],
                minimumSize: const Size.fromHeight(54),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
                elevation: hasSelection ? 4 : 0,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
