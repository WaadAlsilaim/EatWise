import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../dashboard/screens/dashboard_screen.dart';
import '../../../config/api_config.dart';

class ProfileScreen extends StatefulWidget {
  final String accessToken;

  const ProfileScreen({super.key, required this.accessToken});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  // المتحكمات بالنصوص
  final TextEditingController nameController = TextEditingController();
  final TextEditingController heightController = TextEditingController();
  final TextEditingController weightController = TextEditingController();
  final TextEditingController ageController = TextEditingController();

  // القيم المختارة
  String selectedGoal = "Weight Loss";
  String selectedHealth = "None";
  List<String> selectedAllergies = [];

  bool isLoading = false;
  bool isFetching = true;

  // الخيارات المتاحة
  final List<String> goalOptions = ["Weight Loss", "Maintain", "Muscle Gain"];
  final List<String> healthOptions = ["None", "Diabetes", "Blood Pressure", "Heart Disease"];
  final List<String> allergyOptions = ["Dairy", "Peanuts", "Gluten", "Shellfish", "Soy", "Eggs"];

  @override
  void initState() {
    super.initState();
    fetchProfile(); // جلب البيانات عند فتح الصفحة
  }

  // جلب بيانات المستخدم من السيرفر
  Future<void> fetchProfile() async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConfig.baseUrl}/api/accounts/me/"),
        headers: {"Authorization": "Bearer ${widget.accessToken}"},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          nameController.text = data["full_name"] ?? "";
          heightController.text = data["height"]?.toString() ?? "";
          weightController.text = data["weight"]?.toString() ?? "";
          ageController.text = data["age"]?.toString() ?? "";
          selectedGoal = (data["health_goal"] != null &&
                  goalOptions.contains(data["health_goal"]))
              ? data["health_goal"]
              : "Weight Loss";
          selectedHealth = (data["health_condition"] != null &&
                  healthOptions.contains(data["health_condition"]))
                ? data["health_condition"]
                : "None";
          
          if (data["allergies"] != null && data["allergies"] != "None") {
            selectedAllergies = (data["allergies"] as String).split(', ');
          }
        });
      }
    } catch (e) {
      _showSnackBar("Failed to load profile", Colors.red);
    }
    setState(() => isFetching = false);
  }

  // حفظ التعديلات وإرسالها للسيرفر
  Future<void> saveProfile() async {
    setState(() => isLoading = true);
    try {
      final response = await http.patch(
        Uri.parse("${ApiConfig.baseUrl}/api/accounts/me/update/"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer ${widget.accessToken}",
        },
        body: jsonEncode({
          "full_name": nameController.text,
          "height": double.tryParse(heightController.text),
          "weight": double.tryParse(weightController.text),
          "age": int.tryParse(ageController.text),
          "health_goal": selectedGoal,
          "health_condition": selectedHealth,
          "allergies": selectedAllergies.join(', '),
        }),
      );

      if (response.statusCode == 200) {
        _showSnackBar("Profile updated successfully ✅", Colors.green);
        // الانتقال للداشبورد بعد الحفظ بنجاح
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => DashboardScreen(accessToken: widget.accessToken)),
          (route) => false,
        );
      } else {
        _showSnackBar("Update failed ❌", Colors.red);
      }
    } catch (e) {
      _showSnackBar("Server error ❌", Colors.red);
    }
    setState(() => isLoading = false);
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message), backgroundColor: color));
  }

  @override
  Widget build(BuildContext context) {
    if (isFetching) return const Scaffold(body: Center(child: CircularProgressIndicator()));

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Personalize your\nplan", 
              style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, height: 1.2)),
            const SizedBox(height: 10),
            const Text("You can update your information anytime to keep your plan accurate.", 
              style: TextStyle(color: Colors.grey, fontSize: 16)),
            const SizedBox(height: 30),

            _buildSectionLabel("Full Name"),
            _buildTextField(nameController, "Enter name", icon: Icons.person_outline),

            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(child: _buildInputBox("Height", heightController, "cm")),
                const SizedBox(width: 15),
                Expanded(child: _buildInputBox("Weight", weightController, "kg")),
                const SizedBox(width: 15),
                Expanded(child: _buildInputBox("Age", ageController, "yrs")),
              ],
            ),

            const SizedBox(height: 20),
            _buildSectionLabel("Health Goal"),
            _buildDropdown(selectedGoal, goalOptions, (val) => setState(() => selectedGoal = val!)),

            const SizedBox(height: 20),
            _buildSectionLabel("Health Condition"),
            _buildDropdown(selectedHealth, healthOptions, (val) => setState(() => selectedHealth = val!)),

            const SizedBox(height: 20),
            _buildSectionLabel("Allergies"),
            Wrap(
              spacing: 8,
              children: allergyOptions.map((allergy) {
                final isSelected = selectedAllergies.contains(allergy);
                return FilterChip(
                  label: Text(allergy),
                  selected: isSelected,
                  onSelected: (bool selected) {
                    setState(() {
                      selected ? selectedAllergies.add(allergy) : selectedAllergies.remove(allergy);
                    });
                  },
                  selectedColor: const Color(0xFFA5D6A7).withOpacity(0.5),
                  checkmarkColor: Colors.green[800],
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                );
              }).toList(),
            ),

            const SizedBox(height: 40),
            SizedBox(
              width: double.infinity,
              height: 60,
              child: ElevatedButton(
                onPressed: isLoading ? null : saveProfile,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4CAF50),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  elevation: 0,
                ),
                child: isLoading 
                  ? const CircularProgressIndicator(color: Colors.white) 
                  : const Text("Save & Continue", style: TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  // --- أدوات بناء واجهة المستخدم (Widgets) ---

  Widget _buildSectionLabel(String label) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
  );

  Widget _buildTextField(TextEditingController controller, String hint, {IconData? icon}) => Container(
    decoration: BoxDecoration(color: const Color(0xFFF7F8F9), borderRadius: BorderRadius.circular(15)),
    child: TextField(
      controller: controller,
      decoration: InputDecoration(hintText: hint, prefixIcon: icon != null ? Icon(icon, color: Colors.grey) : null, border: InputBorder.none, contentPadding: const EdgeInsets.all(18)),
    ),
  );

  Widget _buildInputBox(String label, TextEditingController controller, String suffix) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
      const SizedBox(height: 5),
      Container(
        decoration: BoxDecoration(color: const Color(0xFFF7F8F9), borderRadius: BorderRadius.circular(15)),
        child: TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          textAlign: TextAlign.center,
          decoration: InputDecoration(suffixText: suffix, border: InputBorder.none, contentPadding: const EdgeInsets.all(15)),
        ),
      ),
    ],
  );

  Widget _buildDropdown(String value, List<String> items, Function(String?) onChanged) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 15),
    decoration: BoxDecoration(color: const Color(0xFFF7F8F9), borderRadius: BorderRadius.circular(15)),
    child: DropdownButtonHideUnderline(
      child: DropdownButton<String>(
        value: value,
        isExpanded: true,
        items: items.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
        onChanged: onChanged,
      ),
    ),
  );
}


