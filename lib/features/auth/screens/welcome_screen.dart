import 'package:flutter/material.dart';
import 'login_screen.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFFE8F5E9),
              Color(0xFFFFFFFF),
            ],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 28),
            child: Column(
              children: [
                const Spacer(flex: 2),

                // المربع الأبيض المحيط بالأيقونة
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(35),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 20,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: Center(
                    child: Image.asset(
                      'assets/images/green_cart.png',
                      width: 70,
                      height: 70,
                      fit: BoxFit.contain,
                      // Graceful fallback if asset is missing
                      errorBuilder: (_, __, ___) => const Icon(
                        Icons.shopping_basket,
                        size: 60,
                        color: Color(0xFF4CAF50),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 40),

                // اسم التطبيق
                const Text(
                  "EatWise",
                  style: TextStyle(
                    fontSize: 48,
                    fontWeight: FontWeight.w900,
                    color: Color(0xFF1A1A1A),
                    letterSpacing: -1.5,
                  ),
                ),

                const SizedBox(height: 15),

                // الوصف
                const Text(
                  "Your smart nutrition assistant &\ncalorie tracker.",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 18,
                    color: Color(0xFF7D848D),
                    height: 1.5,
                    fontWeight: FontWeight.w500,
                  ),
                ),

                const Spacer(flex: 3),

                // زر "ابدأ الآن" — أبسط وأكثر استقراراً من SlideAction
                // الذي كان يسبب أخطاء "Invalid argument(s): 0.0" متكررة
                Padding(
                  padding: const EdgeInsets.only(bottom: 40),
                  child: SizedBox(
                    width: double.infinity,
                    height: 64,
                    child: ElevatedButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const LoginScreen(),
                          ),
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF4CAF50),
                        foregroundColor: Colors.white,
                        elevation: 5,
                        shadowColor: const Color(0xFF4CAF50).withOpacity(0.4),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(20),
                        ),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            "Get Started",
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          SizedBox(width: 10),
                          Icon(Icons.arrow_forward_ios, size: 18),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
