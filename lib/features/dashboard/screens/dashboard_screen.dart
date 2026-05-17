import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

// --- استيرادات المشروع ---
import '../../profile/screens/profile_screen.dart';
import '../../more/screens/more_screen.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/calorie_circle.dart';
import '../widgets/macro_progress.dart';
import '../widgets/feature_card.dart';
import '../widgets/eatwise_options_sheet.dart';
import '../../meals/services/meal_service.dart';
import '../../dashboard/models/food_model.dart';
import '../../products/screens/products_screen.dart';
import '../../meals/screens/meals_screen.dart'; // تأكد من استيراد صفحة الوجبات المحدثة
import '../../image_analysis/screens/image_result_screen.dart';
import '../../activity/screens/activity_screen.dart';
import '../../recipes/screens/recipes_screen.dart';
import '../../../config/api_config.dart';

class DashboardScreen extends StatefulWidget {
  final String accessToken;

  const DashboardScreen({super.key, required this.accessToken});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? profileData;
  Map<String, dynamic>? dailySummary;
  bool isLoading = true;
  int _currentIndex = 0;

  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    await Future.wait([_loadProfile(), _loadDailySummary()]);
    if (mounted) setState(() => isLoading = false);
  }

  Future<void> _loadProfile() async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConfig.baseUrl}/api/accounts/me/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (response.statusCode == 200) {
        profileData = jsonDecode(response.body);
      }
    } catch (_) {}
  }

  Future<void> _loadDailySummary() async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConfig.baseUrl}/api/accounts/daily-summary/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );
      if (response.statusCode == 200) {
        dailySummary = jsonDecode(response.body);
      }
    } catch (_) {}
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? pickedFile =
          await _picker.pickImage(source: source, imageQuality: 85);
      if (pickedFile == null) return;

      final File imageFile = File(pickedFile.path);

      // Show a blocking "analyzing" dialog
      if (!mounted) return;
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (_) => const Center(
          child: Card(
            margin: EdgeInsets.all(40),
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(color: Color(0xFF4CAF50)),
                  SizedBox(height: 16),
                  Text("Analyzing your photo…",
                      style: TextStyle(fontWeight: FontWeight.bold)),
                  SizedBox(height: 6),
                  Text("This takes a few seconds the first time.",
                      style: TextStyle(fontSize: 12, color: Colors.grey)),
                ],
              ),
            ),
          ),
        ),
      );

      // Upload to the backend
      try {
        final request = http.MultipartRequest(
          'POST',
          Uri.parse('${ApiConfig.baseUrl}/analyze-image'),
        );
        request.headers['Authorization'] = 'Bearer ${widget.accessToken}';
        request.files.add(
          await http.MultipartFile.fromPath('image', imageFile.path),
        );

        final streamed = await request.send();
        final response = await http.Response.fromStream(streamed);

        if (!mounted) return;
        Navigator.of(context, rootNavigator: true).pop(); // close dialog

        if (response.statusCode == 200) {
          final Map<String, dynamic> data = jsonDecode(response.body);
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ImageResultScreen(
                result: data,
                imagePath: imageFile.path,
                accessToken: widget.accessToken,
              ),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text("Analysis failed (${response.statusCode})"),
              backgroundColor: Colors.red,
            ),
          );
        }
      } catch (e) {
        if (!mounted) return;
        Navigator.of(context, rootNavigator: true).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Connection error: $e"),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      debugPrint("Error picking image: $e");
    }
  }

  void _showAddOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => EatWiseOptionsSheet(
        onScanTap: () {
          Navigator.pop(context);
          _pickImage(ImageSource.camera);
        },
        onUploadTap: () {
          Navigator.pop(context);
          _pickImage(ImageSource.gallery);
        },
      ),
    );
  }

  void _goToProfile() async {
    final updated = await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => ProfileScreen(accessToken: widget.accessToken)),
    );
    if (updated == true) _loadProfile();
  }

  Widget _getBody() {
    switch (_currentIndex) {
      case 0:
        return _dashboardContent(profileData?["full_name"] ?? "User");
      case 1:
        return ProductsScreen(accessToken: widget.accessToken);
      case 2:
        // شاشة الوجبات التي تعمل كـ Saved Recipes
        return MealsScreen(accessToken: widget.accessToken); 
      case 3:
        return AiRecipesScreen(accessToken: widget.accessToken);
      case 4:
        return MoreScreen(accessToken: widget.accessToken);
      default:
        return const Center(child: Text("Page not found"));
    }
  }

  Widget _dashboardContent(String name) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 40),
          _buildHeader(name),
          const SizedBox(height: 30),
          _buildDailySummary(),
          const SizedBox(height: 30),

          // 3. Quick Actions (Products & Saved Recipes)
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 125,
                  child: GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => ProductsScreen(accessToken: widget.accessToken)),
                      );
                    },
                    child: const FeatureCard(
                      title: "My Products",
                      icon: Icons.inventory_2_outlined,
                      iconColor: Color(0xFF4CAF50),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 15),
              Expanded(
                child: SizedBox(
                  height: 125,
                  child: GestureDetector(
                    onTap: () {
                      // ننتقل لشاشة الوجبات (التي أصبحت شاشة المحفوظات)
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => MealsScreen(accessToken: widget.accessToken)),
                      );
                    },
                    child: const FeatureCard(
                      title: "Saved Recipes",
                      icon: Icons.restaurant_outlined,
                      iconColor: Color(0xFF4CAF50),
                    ),
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 15),

          // 4. Workout Card (عريض ومتناسق)
          _buildWorkoutCard(),

          const SizedBox(height: 120),
        ],
      ),
    );
  }

  Widget _buildHeader(String name) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            GestureDetector(
              onTap: _goToProfile,
              child: const CircleAvatar(
                radius: 28,
                backgroundColor: Colors.white,
                child: Icon(Icons.person, color: Colors.black, size: 30),
              ),
            ),
            const SizedBox(width: 15),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("Healthy choices, happy life", style: TextStyle(fontSize: 13, color: Colors.grey)),
                Text(name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              ],
            ),
          ],
        ),
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withOpacity(0.9)),
          child: const Icon(Icons.notifications_none, size: 26),
        ),
      ],
    );
  }

  Widget _buildDailySummary() {
    // Real values from /api/accounts/daily-summary/ (falls back to 0 until loaded).
    // Every value is hardened against null / NaN / Infinity to avoid
    // "Invalid argument(s): 0.0" errors during the progress arc paint.
    double _toDouble(dynamic v, [double fallback = 0]) {
      if (v == null) return fallback;
      if (v is num) {
        final d = v.toDouble();
        if (d.isNaN || d.isInfinite) return fallback;
        return d;
      }
      return fallback;
    }

    final s = dailySummary;
    final target = _toDouble(s?["target_kcal"], 2000);
    final consumed = _toDouble(s?["consumed_kcal"], 0);
    final burned = _toDouble(s?["burned_kcal"], 0);
    final remaining = _toDouble(s?["remaining_kcal"], target);
    final net = (consumed - burned).clamp(0.0, double.maxFinite).toDouble();

    double progress = 0.0;
    if (target > 0) {
      final raw = net / target;
      if (!raw.isNaN && !raw.isInfinite) {
        progress = raw.clamp(0.0, 1.0).toDouble();
      }
    }

    final p = (s?["protein"] ?? {"consumed": 0, "target": 125}) as Map;
    final c = (s?["carbs"] ?? {"consumed": 0, "target": 250}) as Map;
    final f = (s?["fat"] ?? {"consumed": 0, "target": 55}) as Map;

    double _pct(dynamic consumed, dynamic target) {
      final c = _toDouble(consumed);
      final t = _toDouble(target);
      if (t <= 0) return 0;
      final r = c / t;
      if (r.isNaN || r.isInfinite) return 0;
      return r.clamp(0.0, 1.0).toDouble();
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 20,
              offset: const Offset(0, 10)),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("Daily Summary",
                  style:
                      TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              Text(
                "${consumed.toInt()} / ${target.toInt()} kcal",
                style:
                    const TextStyle(color: Colors.grey, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 20),
          CalorieCircle(
            progress: progress,
            kcalLeft: remaining.toInt(),
          ),
          const SizedBox(height: 8),
          if (burned > 0)
            Text("🔥 ${burned.toStringAsFixed(0)} kcal burned today",
                style: const TextStyle(
                    color: Color(0xFF4CAF50),
                    fontWeight: FontWeight.w600,
                    fontSize: 12)),
          const SizedBox(height: 18),
          MacroProgress(
            label: "Protein",
            amount: "${p["consumed"]}g / ${p["target"]}g",
            progress: _pct(p["consumed"], p["target"]),
            color: const Color(0xFFB6F0B8),
          ),
          MacroProgress(
            label: "Carbs",
            amount: "${c["consumed"]}g / ${c["target"]}g",
            progress: _pct(c["consumed"], c["target"]),
            color: const Color(0xFFFBD49B),
          ),
          MacroProgress(
            label: "Fat",
            amount: "${f["consumed"]}g / ${f["target"]}g",
            progress: _pct(f["consumed"], f["target"]),
            color: const Color(0xFF9CEBFE),
          ),
        ],
      ),
    );
  }

  Widget _buildWorkoutCard() {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ActivityScreen(accessToken: widget.accessToken),
          ),
        );
      },
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(25),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 20,
              offset: const Offset(0, 10),
            )
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(
                color: const Color(0xFFE8F5E9),
                borderRadius: BorderRadius.circular(15),
              ),
              child: const Icon(Icons.fitness_center, color: Color(0xFF4CAF50), size: 30),
            ),
            const SizedBox(width: 20),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Workouts Routine",
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 4),
                  Text(
                    "Keep your body active and track your progress",
                    style: TextStyle(fontSize: 13, color: Colors.grey),
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios, size: 18, color: Colors.grey),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));

    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      body: Stack(
        children: [
          Container(
            height: 230,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFFD6E2D9), Color(0xFFF3F6F4)],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
          SafeArea(child: _getBody()),
        ],
      ),
      bottomNavigationBar: CustomBottomNavBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
      ),
      floatingActionButton: GestureDetector(
        onTap: () => _showAddOptions(context),
        child: Container(
          height: 70, width: 70,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: const Color(0xFF4CAF50),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.15), blurRadius: 20, offset: const Offset(0, 10))],
          ),
          child: const Icon(Icons.add, size: 32, color: Colors.white),
        ),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
    );
  }
}