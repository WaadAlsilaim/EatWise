import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../../widgets/food_image.dart';
import '../../../config/api_config.dart';

/// Browse the catalog of all foods and add any of them to the user's pantry.
class AddProductScreen extends StatefulWidget {
  final String accessToken;
  const AddProductScreen({super.key, required this.accessToken});

  @override
  State<AddProductScreen> createState() => _AddProductScreenState();
}

class _AddProductScreenState extends State<AddProductScreen> {
  String get _base => ApiConfig.baseUrl;

  List<dynamic> all = [];
  Set<int> alreadyInPantry = {};
  Set<int> justAdded = {};
  bool isLoading = true;
  String _query = "";
  Timer? _searchDebounce;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    super.dispose();
  }

  Future<void> _loadAll() async {
    setState(() => isLoading = true);
    try {
      final results = await Future.wait([
        http.get(Uri.parse("$_base/api/products/products/?limit=100")),
        http.get(
          Uri.parse("$_base/api/pantry/"),
          headers: {"Authorization": "Bearer ${widget.accessToken}"},
        ),
      ]);
      if (results[0].statusCode == 200) all = jsonDecode(results[0].body);
      if (results[1].statusCode == 200) {
        final pantry = jsonDecode(results[1].body) as List;
        alreadyInPantry = pantry
            .map<int>((p) => (p["food_id"] ?? 0) as int)
            .toSet();
      }
    } catch (_) {}
    if (mounted) setState(() => isLoading = false);
  }

  Future<void> _addToPantry(dynamic item) async {
    final id = item["id"] as int;
    setState(() {
      justAdded.add(id);
      alreadyInPantry.add(id);
    });
    try {
      final r = await http.post(
        Uri.parse("$_base/api/pantry/"),
        headers: {
          "Authorization": "Bearer ${widget.accessToken}",
          "Content-Type": "application/json",
        },
        body: jsonEncode({"food_id": id, "quantity": 1, "unit": "piece"}),
      );
      if (r.statusCode != 201 && r.statusCode != 200) {
        setState(() {
          justAdded.remove(id);
          alreadyInPantry.remove(id);
        });
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("Failed to add (${r.statusCode})"),
          backgroundColor: Colors.red,
        ));
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("Added ${item["name"]} to your pantry"),
          backgroundColor: const Color(0xFF4CAF50),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 1),
        ));
      }
    } catch (e) {
      setState(() {
        justAdded.remove(id);
        alreadyInPantry.remove(id);
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("Network error: $e"),
          backgroundColor: Colors.red,
        ));
      }
    }
  }

  List<dynamic> get _filtered {
    if (_query.isEmpty) return all;
    final q = _query.toLowerCase();
    return all.where((item) {
      final name = (item["name"] ?? "").toString().toLowerCase();
      final nameAr = (item["name_ar"] ?? "").toString().toLowerCase();
      final cat = (item["category"] ?? "").toString().toLowerCase();
      return name.contains(q) || nameAr.contains(q) || cat.contains(q);
    }).toList();
  }

  void _onSearch(String v) {
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 200), () {
      if (mounted) setState(() => _query = v);
    });
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
          onPressed: () => Navigator.pop(context, justAdded.isNotEmpty),
        ),
        title: const Text("Add Product",
            style: TextStyle(
                color: Colors.black,
                fontWeight: FontWeight.bold,
                fontSize: 18)),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: TextField(
              onChanged: _onSearch,
              decoration: InputDecoration(
                hintText: "Search food (English or Arabic)…",
                prefixIcon: const Icon(Icons.search, color: Colors.grey),
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(15),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
          Expanded(
            child: isLoading
                ? const Center(
                    child:
                        CircularProgressIndicator(color: Color(0xFF4CAF50)))
                : _filtered.isEmpty
                    ? const Center(
                        child: Text("No matches.",
                            style: TextStyle(color: Colors.grey)))
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 80),
                        itemCount: _filtered.length,
                        itemBuilder: (_, i) => _itemRow(_filtered[i]),
                      ),
          ),
        ],
      ),
      bottomNavigationBar: justAdded.isEmpty
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.pop(context, true),
                  icon: const Icon(Icons.check),
                  label: Text(
                      "Done (${justAdded.length} added)",
                      style: const TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 16)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF4CAF50),
                    foregroundColor: Colors.white,
                    minimumSize: const Size.fromHeight(50),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14)),
                  ),
                ),
              ),
            ),
    );
  }

  Widget _itemRow(dynamic item) {
    final id = item["id"] as int;
    final inPantry = alreadyInPantry.contains(id);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          FoodImage(
            emoji: item["emoji"] ?? "🍽️",
            colorHex: item["color_hex"] ?? "#F2F2F2",
            imageUrl: item["image_url"] ?? "",
            size: 48, borderRadius: 12,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item["name"] ?? "",
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 14),
                    overflow: TextOverflow.ellipsis),
                if ((item["name_ar"] ?? "").toString().isNotEmpty)
                  Text(item["name_ar"],
                      style: const TextStyle(
                          color: Colors.grey, fontSize: 11)),
                Text("${item["calories"] ?? 0} kcal / 100g",
                    style: const TextStyle(
                        color: Colors.grey, fontSize: 11)),
              ],
            ),
          ),
          IconButton(
            onPressed: inPantry ? null : () => _addToPantry(item),
            icon: Icon(
              inPantry ? Icons.check_circle : Icons.add_circle_outline,
              color: inPantry
                  ? const Color(0xFF4CAF50)
                  : Colors.grey[400],
              size: 30,
            ),
          ),
        ],
      ),
    );
  }
}
