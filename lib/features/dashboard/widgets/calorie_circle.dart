import 'package:flutter/material.dart';
import 'dart:math';

class CalorieCircle extends StatelessWidget {
  final double progress; // نسبة الحرق 0.0 - 1.0
  final int kcalLeft;

  const CalorieCircle({super.key, this.progress = 0.7, this.kcalLeft = 1450});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 140,
      width: 140,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: const Size(140, 140),
            painter: _CirclePainter(progress),
          ),
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '$kcalLeft',
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Text(
                'Kcal Left',
                style: TextStyle(fontSize: 14, color: Colors.grey),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CirclePainter extends CustomPainter {
  final double progress;

  _CirclePainter(this.progress);

  @override
  void paint(Canvas canvas, Size size) {
    final strokeWidth = 12.0;
    final center = size.center(Offset.zero);
    final radius = (size.width / 2) - strokeWidth / 2;

    // ===== خلفية الدائرة =====
    final bgPaint = Paint()
      ..color = Colors.grey.shade200
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth;

    // ===== لون السايكل (التقدم) =====
    // تم تغييره ليكون نفس لون البروتين في الداشبورد
    final fgPaint = Paint()
      ..color = const Color(0xFF4CAF50)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, bgPaint);

    final double angle = 2 * pi * progress;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -pi / 2,
      angle,
      false,
      fgPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}