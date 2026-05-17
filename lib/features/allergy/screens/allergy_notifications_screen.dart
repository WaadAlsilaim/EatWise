import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../../config/api_config.dart';

class AllergyNotificationsScreen extends StatefulWidget {
  final String accessToken;
  const AllergyNotificationsScreen({super.key, required this.accessToken});

  @override
  State<AllergyNotificationsScreen> createState() =>
      _AllergyNotificationsScreenState();
}

class _AllergyNotificationsScreenState
    extends State<AllergyNotificationsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tab;
  bool loadingPersonal = true;
  bool loadingSfda = true;
  List<dynamic> personal = [];
  List<dynamic> sfda = [];

  String get _base => ApiConfig.baseUrl;

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 2, vsync: this);
    _loadPersonal();
    _loadSfda();
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  Future<void> _loadPersonal() async {
    setState(() => loadingPersonal = true);
    try {
      final r = await http.get(
        Uri.parse("$_base/api/alerts/personal/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (r.statusCode == 200) {
        final List data = jsonDecode(r.body);
        setState(() => personal = data);
      }
    } catch (_) {}
    if (mounted) setState(() => loadingPersonal = false);
  }

  Future<void> _loadSfda() async {
    setState(() => loadingSfda = true);
    try {
      final r = await http.get(Uri.parse("$_base/api/alerts/sfda/"));
      if (r.statusCode == 200) {
        final List data = jsonDecode(r.body);
        setState(() => sfda = data);
      }
    } catch (_) {}
    if (mounted) setState(() => loadingSfda = false);
  }

  Future<void> _acknowledge(int alertId) async {
    try {
      await http.post(
        Uri.parse("$_base/api/alerts/$alertId/ack/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
    } catch (_) {}
    _loadPersonal();
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
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
            "Health Alerts",
            style: TextStyle(
                color: Colors.black, fontWeight: FontWeight.bold, fontSize: 18),
          ),
          bottom: TabBar(
            controller: _tab,
            labelColor: const Color(0xFF4CAF50),
            unselectedLabelColor: Colors.grey,
            indicatorColor: const Color(0xFF4CAF50),
            indicatorWeight: 3,
            tabs: [
              Tab(text: "Personal (${personal.length})"),
              Tab(text: "SFDA (${sfda.length})"),
            ],
          ),
        ),
        body: TabBarView(
          controller: _tab,
          children: [_buildPersonalTab(), _buildSfdaTab()],
        ),
      ),
    );
  }

  Widget _buildPersonalTab() {
    if (loadingPersonal) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF4CAF50)));
    }
    if (personal.isEmpty) {
      return _emptyState(Icons.shield_outlined, "No personal alerts yet",
          "We'll notify you about allergens, your health condition, and SFDA recalls.");
    }
    return RefreshIndicator(
      onRefresh: _loadPersonal,
      color: const Color(0xFF4CAF50),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: personal.length,
        itemBuilder: (_, i) => _personalCard(personal[i]),
      ),
    );
  }

  Widget _buildSfdaTab() {
    if (loadingSfda) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF4CAF50)));
    }
    if (sfda.isEmpty) {
      return _emptyState(Icons.cloud_off_outlined, "No SFDA alerts right now",
          "When new food safety warnings are published, they'll show up here.");
    }
    return RefreshIndicator(
      onRefresh: _loadSfda,
      color: const Color(0xFF4CAF50),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: sfda.length,
        itemBuilder: (_, i) => _sfdaCard(sfda[i]),
      ),
    );
  }

  Widget _personalCard(dynamic a) {
    final kind = (a["kind"] ?? "").toString();
    final ack = a["acknowledged"] == true;
    final icons = {
      "allergen": Icons.warning_amber_rounded,
      "condition": Icons.favorite_border,
      "sfda": Icons.announcement_outlined,
    };
    final colors = {
      "allergen": const Color(0xFFE53935),
      "condition": const Color(0xFFFB8C00),
      "sfda": const Color(0xFF1E88E5),
    };
    final icon = icons[kind] ?? Icons.notifications_none;
    final color = colors[kind] ?? Colors.grey;

    return Dismissible(
      key: ValueKey("pa-${a["id"]}"),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 24),
        color: Colors.grey[200],
        child: const Icon(Icons.check, color: Color(0xFF4CAF50)),
      ),
      onDismissed: (_) => _acknowledge(a["id"] as int),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: ack ? Colors.transparent : color.withOpacity(0.3),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.03),
              blurRadius: 12, offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color),
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
                          a["title"] ?? "",
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                      ),
                      if (!ack)
                        Container(
                          width: 8, height: 8,
                          decoration: BoxDecoration(
                              color: color, shape: BoxShape.circle),
                        ),
                    ],
                  ),
                  if ((a["body"] ?? "").toString().isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(a["body"],
                        style: const TextStyle(
                            color: Colors.grey, fontSize: 13, height: 1.4)),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sfdaCard(dynamic a) {
    final severity = (a["severity"] ?? "medium").toString();
    final color = severity == "high"
        ? const Color(0xFFE53935)
        : severity == "low"
            ? const Color(0xFFFFA726)
            : const Color(0xFFFB8C00);
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 12, offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  severity.toUpperCase(),
                  style: TextStyle(
                      color: color, fontWeight: FontWeight.bold, fontSize: 11),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                (a["alert_type"] ?? "").toString().toUpperCase(),
                style: const TextStyle(
                    color: Colors.grey, fontWeight: FontWeight.bold, fontSize: 11),
              ),
              const Spacer(),
              if ((a["published_at"] ?? "").toString().isNotEmpty)
                Text(
                  _formatDate(a["published_at"].toString()),
                  style: const TextStyle(color: Colors.grey, fontSize: 11),
                ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            (a["title_ar"] ?? "").toString().isNotEmpty
                ? a["title_ar"]
                : (a["title_en"] ?? a["title"] ?? ""),
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
          ),
          if ((a["product_name"] ?? "").toString().isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.inventory_2_outlined,
                    size: 14, color: Colors.grey),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    a["product_name"],
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  String _formatDate(String iso) {
    try {
      final d = DateTime.parse(iso);
      return "${d.day}/${d.month}/${d.year}";
    } catch (_) {
      return "";
    }
  }

  Widget _emptyState(IconData icon, String title, String body) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 12),
            Text(title,
                style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.grey,
                    fontSize: 16)),
            const SizedBox(height: 8),
            Text(body,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey, fontSize: 13)),
          ],
        ),
      ),
    );
  }
}
