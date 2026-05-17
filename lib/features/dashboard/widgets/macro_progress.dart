import 'package:flutter/material.dart';

class MacroProgress extends StatelessWidget {
  final String label;
  final String amount;
  final double progress;
  final Color color;

  const MacroProgress({
    super.key,
    required this.label,
    required this.amount,
    required this.progress,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label,
                  style: const TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w500)),
              Text(amount,
                  style: const TextStyle(
                      fontSize: 14, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 10,
              color: color,
              backgroundColor: Colors.grey.shade200,
            ),
          ),
        ],
      ),
    );
  }
}