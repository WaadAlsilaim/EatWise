import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../../config/api_config.dart';

class ActivityScreen extends StatefulWidget {
  final String accessToken;
  const ActivityScreen({super.key, required this.accessToken});

  @override
  State<ActivityScreen> createState() => _ActivityScreenState();
}

class _ActivityScreenState extends State<ActivityScreen> {
  String get _base => ApiConfig.baseUrl;

  List<dynamic> catalog = [];
  Map<String, dynamic>? summary;
  Map<String, dynamic>? suggestions;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() => isLoading = true);
    await Future.wait([_loadCatalog(), _loadSummary(), _loadSuggestions()]);
    if (mounted) setState(() => isLoading = false);
  }

  Future<void> _loadCatalog() async {
    try {
      final r = await http.get(Uri.parse("$_base/api/activity/catalog/"));
      if (r.statusCode == 200) catalog = jsonDecode(r.body);
    } catch (_) {}
  }

  Future<void> _loadSummary() async {
    try {
      final r = await http.get(
        Uri.parse("$_base/api/activity/summary/?range=week"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (r.statusCode == 200) summary = jsonDecode(r.body);
    } catch (_) {}
  }

  Future<void> _loadSuggestions() async {
    try {
      final r = await http.get(
        Uri.parse("$_base/api/activity/suggestions/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (r.statusCode == 200) suggestions = jsonDecode(r.body);
    } catch (_) {}
  }

  Future<void> _logActivity(Map<String, dynamic> type, double amount) async {
    try {
      final r = await http.post(
        Uri.parse("$_base/api/activity/log/"),
        headers: {
          "Authorization": "Bearer ${widget.accessToken}",
          "Content-Type": "application/json",
        },
        body: jsonEncode({
          "activity_type": type["type"],
          "amount": amount,
          "unit": type["unit"],
        }),
      );
      if (r.statusCode == 201) {
        if (!mounted) return;
        final data = jsonDecode(r.body);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(
              "${type["label_en"]} logged — burned ${data["kcal_burned"]} kcal"),
          backgroundColor: const Color(0xFF4CAF50),
          behavior: SnackBarBehavior.floating,
        ));
        _loadAll();
      } else {
        _showError("Failed to log activity (${r.statusCode})");
      }
    } catch (e) {
      _showError("Network error: $e");
    }
  }

  Future<void> _deleteLog(int id) async {
    try {
      await http.delete(
        Uri.parse("$_base/api/activity/$id/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      _loadAll();
    } catch (_) {}
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: Colors.red,
      behavior: SnackBarBehavior.floating,
    ));
  }

  void _showLogSheet(Map<String, dynamic> type) {
    final controller = TextEditingController(
        text: type["unit"] == "steps" ? "3000" : "30");
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (_) => Padding(
        padding: EdgeInsets.only(
          left: 24, right: 24, top: 24,
          bottom: MediaQuery.of(context).viewInsets.bottom + 24,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 48, height: 4, margin: const EdgeInsets.only(bottom: 14),
              decoration: BoxDecoration(
                color: Colors.grey[300], borderRadius: BorderRadius.circular(4),
              ),
            ),
            Text("Log ${type["label_en"]}",
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text("How much ${type["unit"]}?",
                style: const TextStyle(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 20),
            TextField(
              controller: controller,
              keyboardType: TextInputType.number,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
              decoration: InputDecoration(
                suffixText: type["unit"],
                filled: true,
                fillColor: const Color(0xFFF3F6F4),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(15),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  final v = double.tryParse(controller.text) ?? 0;
                  if (v <= 0) return;
                  Navigator.pop(context);
                  _logActivity(type, v);
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4CAF50),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
                child: const Text("Log Activity",
                    style:
                        TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0.5,
        centerTitle: true,
        title: const Text(
          "Activity",
          style: TextStyle(
              color: Colors.black, fontWeight: FontWeight.bold, fontSize: 18),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Colors.black, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF4CAF50)))
          : RefreshIndicator(
              onRefresh: _loadAll,
              color: const Color(0xFF4CAF50),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _weeklySummary(),
                  const SizedBox(height: 16),
                  if (suggestions != null) _suggestionCard(),
                  const SizedBox(height: 18),
                  const Text("Log new activity",
                      style: TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 10),
                  _activityGrid(),
                  const SizedBox(height: 22),
                  const Text("Recent activity",
                      style: TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 10),
                  _recentList(),
                ],
              ),
            ),
    );
  }

  Widget _weeklySummary() {
    final total = (summary?["total_kcal_burned"] ?? 0) as num;
    final entries = (summary?["total_entries"] ?? 0) as num;
    final byType = (summary?["by_type"] ?? {}) as Map;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF4CAF50), Color(0xFF2E7D32)],
          begin: Alignment.topLeft, end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("THIS WEEK",
              style: TextStyle(
                  color: Colors.white70,
                  fontWeight: FontWeight.bold,
                  fontSize: 11)),
          const SizedBox(height: 8),
          Text("${total.toInt()} kcal",
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 32,
                  fontWeight: FontWeight.bold)),
          Text("$entries activities logged",
              style: const TextStyle(color: Colors.white70, fontSize: 13)),
          if (byType.isNotEmpty) ...[
            const SizedBox(height: 14),
            Wrap(
              spacing: 8, runSpacing: 6,
              children: byType.entries
                  .take(4)
                  .map<Widget>((e) => Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.18),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          "${e.key} ${e.value.toString()} kcal",
                          style: const TextStyle(
                              color: Colors.white, fontSize: 11),
                        ),
                      ))
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _suggestionCard() {
    final tips = (suggestions!["tips"] as List?) ?? [];
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8E1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFFFE0A3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.lightbulb_outline, color: Color(0xFFE6A100)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("Today's suggestion",
                    style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF8C6A00),
                        fontSize: 13)),
                const SizedBox(height: 4),
                ...tips.map<Widget>((t) => Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(t.toString(),
                          style: const TextStyle(
                              color: Color(0xFF8C6A00), fontSize: 13)),
                    )),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _activityGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        crossAxisSpacing: 10, mainAxisSpacing: 10,
        childAspectRatio: 0.85,
      ),
      itemCount: catalog.length,
      itemBuilder: (_, i) {
        final t = catalog[i] as Map<String, dynamic>;
        return GestureDetector(
          onTap: () => _showLogSheet(t),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 8,
                    offset: const Offset(0, 4)),
              ],
            ),
            padding: const EdgeInsets.all(8),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 42, height: 42,
                  decoration: BoxDecoration(
                    color: _parseColor(t["color_hex"]),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  alignment: Alignment.center,
                  child: Text(t["emoji"] ?? "🏃",
                      style: const TextStyle(fontSize: 22)),
                ),
                const SizedBox(height: 6),
                Text(t["label_en"] ?? "",
                    style: const TextStyle(
                        fontSize: 11, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _recentList() {
    final entries = (summary?["entries"] as List?) ?? [];
    if (entries.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: Colors.white, borderRadius: BorderRadius.circular(20),
        ),
        child: const Center(
          child: Text("No activity yet — tap an icon above to log your first one.",
              style: TextStyle(color: Colors.grey)),
        ),
      );
    }
    return Column(
      children: entries.take(10).map<Widget>((e) {
        return Dismissible(
          key: ValueKey("log-${e["id"]}"),
          direction: DismissDirection.endToStart,
          background: Container(
            alignment: Alignment.centerRight,
            padding: const EdgeInsets.only(right: 24),
            color: Colors.red[50],
            child: const Icon(Icons.delete_outline, color: Colors.red),
          ),
          onDismissed: (_) => _deleteLog(e["id"] as int),
          child: Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white, borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                Container(
                  width: 42, height: 42,
                  decoration: BoxDecoration(
                    color: _parseColor(e["color_hex"]),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  alignment: Alignment.center,
                  child: Text(e["emoji"] ?? "🏃",
                      style: const TextStyle(fontSize: 20)),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(e["label_en"] ?? "",
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 14)),
                      Text(
                        "${(e["amount"] ?? 0).toString()} ${e["unit"] ?? ''} • ${_relTime(e["occurred_at"] ?? '')}",
                        style: const TextStyle(color: Colors.grey, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                Text("${(e["kcal_burned"] ?? 0).toString()} kcal",
                    style: const TextStyle(
                        color: Color(0xFF4CAF50), fontWeight: FontWeight.bold)),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  String _relTime(String iso) {
    try {
      final d = DateTime.parse(iso);
      final diff = DateTime.now().toUtc().difference(d.toUtc());
      if (diff.inMinutes < 1) return "just now";
      if (diff.inMinutes < 60) return "${diff.inMinutes} min ago";
      if (diff.inHours < 24) return "${diff.inHours}h ago";
      return "${diff.inDays}d ago";
    } catch (_) {
      return "";
    }
  }

  Color _parseColor(String? hex) {
    if (hex == null || hex.isEmpty) return const Color(0xFFF2F2F2);
    var h = hex.replaceAll('#', '').trim();
    if (h.length == 6) h = 'FF$h';
    try {
      return Color(int.parse(h, radix: 16));
    } catch (_) {
      return const Color(0xFFF2F2F2);
    }
  }
}
