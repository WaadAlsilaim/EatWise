import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'image_result_screen.dart';
import '../../../config/api_config.dart';

/// A standalone screen that lets the user pick an image and analyze it.
/// Kept for compatibility — the main entry point is now the + button in
/// DashboardScreen.
class ImageAnalysisScreen extends StatefulWidget {
  final String accessToken;

  const ImageAnalysisScreen({super.key, required this.accessToken});

  @override
  State<ImageAnalysisScreen> createState() => _ImageAnalysisScreenState();
}

class _ImageAnalysisScreenState extends State<ImageAnalysisScreen> {
  bool isAnalyzing = false;
  final ImagePicker _picker = ImagePicker();

  Future<void> _pickAndAnalyze(ImageSource source) async {
    final picked = await _picker.pickImage(source: source, imageQuality: 85);
    if (picked == null) return;
    await _analyze(File(picked.path));
  }

  Future<void> _analyze(File imageFile) async {
    setState(() => isAnalyzing = true);
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
      setState(() => isAnalyzing = false);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        Navigator.pushReplacement(
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
              backgroundColor: Colors.red),
        );
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => isAnalyzing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Analyze Meal"),
        elevation: 0,
        backgroundColor: Colors.transparent,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Center(
        child: isAnalyzing
            ? Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(color: Color(0xFF4CAF50)),
                  const SizedBox(height: 20),
                  Text("Analyzing your meal…",
                      style: TextStyle(color: Colors.grey[600])),
                ],
              )
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                    icon: const Icon(Icons.camera_alt,
                        size: 100, color: Color(0xFF4CAF50)),
                    onPressed: () => _pickAndAnalyze(ImageSource.camera),
                  ),
                  const SizedBox(height: 20),
                  const Text("Tap the camera to capture a meal"),
                  const SizedBox(height: 30),
                  TextButton.icon(
                    onPressed: () => _pickAndAnalyze(ImageSource.gallery),
                    icon: const Icon(Icons.photo_library),
                    label: const Text("Or upload from gallery"),
                  ),
                ],
              ),
      ),
    );
  }
}
