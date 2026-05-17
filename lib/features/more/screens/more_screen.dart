import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../profile/screens/profile_screen.dart';
import '../../allergy/screens/allergy_notifications_screen.dart';
import '../../auth/screens/welcome_screen.dart';
import '../../../config/api_config.dart';

class MoreScreen extends StatefulWidget {
  final String accessToken;
  const MoreScreen({super.key, required this.accessToken});

  @override
  State<MoreScreen> createState() => _MoreScreenState();
}

class _MoreScreenState extends State<MoreScreen> {
  String get _base => ApiConfig.baseUrl;
  Map<String, dynamic>? profileData;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final response = await http.get(
        Uri.parse("$_base/api/accounts/me/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );

      if (response.statusCode == 200) {
        setState(() {
          profileData = jsonDecode(response.body);
          isLoading = false;
        });
      } else {
        setState(() => isLoading = false);
      }
    } catch (_) {
      setState(() => isLoading = false);
    }
  }

  Future<void> _clearLocalSession() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('accessToken');
      await prefs.remove('refreshToken');
    } catch (_) {}
  }

  Future<void> _doLogout() async {
    // Best-effort server-side token revocation
    try {
      await http.post(
        Uri.parse("$_base/api/accounts/logout/"),
        headers: {
          "Authorization": "Bearer ${widget.accessToken}",
          "Content-Type": "application/json",
        },
        body: jsonEncode({}),
      );
    } catch (_) {}
    await _clearLocalSession();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const WelcomeScreen()),
      (route) => false,
    );
  }

  Future<void> _doDelete() async {
    try {
      final r = await http.delete(
        Uri.parse("$_base/api/accounts/me/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (r.statusCode != 204 && r.statusCode != 200) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
                content: Text("Delete failed (${r.statusCode})"),
                backgroundColor: Colors.red),
          );
        }
        return;
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Network error: $e"), backgroundColor: Colors.red),
        );
      }
      return;
    }
    await _clearLocalSession();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const WelcomeScreen()),
      (route) => false,
    );
  }

  void _confirm({
    required String title,
    required String body,
    required String confirmText,
    required Color confirmColor,
    required VoidCallback onConfirm,
  }) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: Text(title,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
        content: Text(body),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              onConfirm();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: confirmColor, foregroundColor: Colors.white,
            ),
            child: Text(confirmText),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF9F9F9),
      appBar: AppBar(
        title: const Text("More",
            style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _buildSectionHeader("ACCOUNT"),
          _buildCard(
            context,
            icon: Icons.person_outline,
            title: profileData?["full_name"] ?? "User",
            subtitle: profileData?["health_goal"] ?? "",
            isProfile: true,
            onTap: () async {
              final updated = await Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) =>
                        ProfileScreen(accessToken: widget.accessToken)),
              );
              if (updated == true) _loadProfile();
            },
          ),

          const SizedBox(height: 25),
          _buildSectionHeader("PREFERENCES"),
          _buildCard(
            context,
            icon: Icons.shield_outlined,
            title: "Health Alerts",
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                  builder: (_) => AllergyNotificationsScreen(
                      accessToken: widget.accessToken)),
            ),
          ),

          const SizedBox(height: 25),
          _buildSectionHeader("SYSTEM"),
          _buildCard(
            context,
            icon: Icons.logout,
            title: "Log Out",
            isLogout: true,
            onTap: () => _confirm(
              title: "Log out?",
              body: "You can log back in any time with your phone number.",
              confirmText: "Log out",
              confirmColor: Colors.redAccent,
              onConfirm: _doLogout,
            ),
          ),
          const SizedBox(height: 10),
          _buildCard(
            context,
            icon: Icons.delete_outline,
            title: "Delete Account",
            isDanger: true,
            onTap: () => _confirm(
              title: "Delete account permanently?",
              body:
                  "All your data (profile, saved meals, activity, alerts) will be permanently removed. This cannot be undone.",
              confirmText: "Delete forever",
              confirmColor: const Color(0xFFB71C1C),
              onConfirm: _doDelete,
            ),
          ),
          const SizedBox(height: 20),
          // Medical disclaimer (required by SFDA General Wellness classification)
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFF5F5F5),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Text(
              "⚠ Not intended for medical purposes. For general wellness only.\n"
              "هذا التطبيق غير مخصص للأغراض الطبية — للعافية العامة فقط.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ),
          const SizedBox(height: 30),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) => Padding(
        padding: const EdgeInsets.only(bottom: 8, left: 4),
        child: Text(title,
            style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.grey,
                fontSize: 12)),
      );

  Widget _buildCard(
    BuildContext context, {
    required IconData icon,
    required String title,
    String? subtitle,
    String? badge,
    bool isProfile = false,
    bool isLogout = false,
    bool isDanger = false,
    required VoidCallback onTap,
  }) {
    final color = isDanger
        ? const Color(0xFFB71C1C)
        : isLogout
            ? Colors.redAccent
            : Colors.black;
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      color: Colors.white,
      child: ListTile(
        onTap: onTap,
        leading: isProfile
            ? Container(
                padding: const EdgeInsets.all(8),
                decoration: const BoxDecoration(
                    color: Color(0xFFF3F6F4), shape: BoxShape.circle),
                child: const Icon(Icons.person, color: Colors.black),
              )
            : Icon(icon, color: color == Colors.black ? Colors.grey : color),
        title: Text(title,
            style:
                TextStyle(fontWeight: FontWeight.bold, color: color)),
        subtitle: (subtitle != null && subtitle.isNotEmpty)
            ? Text(subtitle, style: const TextStyle(color: Colors.grey))
            : null,
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (badge != null)
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10)),
                child: Text(badge,
                    style:
                        const TextStyle(fontSize: 12, color: Colors.orange)),
              ),
            if (!isLogout && !isDanger) const SizedBox(width: 8),
            if (!isLogout && !isDanger)
              const Icon(Icons.arrow_forward_ios, size: 16),
          ],
        ),
      ),
    );
  }
}
