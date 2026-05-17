import 'package:flutter/material.dart';
import 'features/auth/screens/welcome_screen.dart';

void main() {
  runApp(const EatWiseApp());
}

class EatWiseApp extends StatelessWidget {
  const EatWiseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'EatWise',
      theme: ThemeData(
        useMaterial3: true,
        platform: TargetPlatform.iOS,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF27AE60),
        ),
        scaffoldBackgroundColor: const Color(0xFFF1F8F4),
      ),
      home: const WelcomeScreen(),
    );
  }
}