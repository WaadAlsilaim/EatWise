import 'package:flutter/material.dart';

class CustomBottomNavBar extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;

  const CustomBottomNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return BottomAppBar(
      shape: const CircularNotchedRectangle(),
      notchMargin: 8.0,
      clipBehavior: Clip.antiAlias,
      child: Container(
        height: 70,
        color: Colors.white,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            // Dashboard
            _buildNavItem(icon: Icons.grid_view_rounded, label: "Dashboard", isSelected: currentIndex == 0, onTap: () => onTap(0)),
            
            const SizedBox(width: 40), // مساحة للزر العائم في المنتصف

            // More
            _buildNavItem(icon: Icons.more_horiz, label: "More", isSelected: currentIndex == 4, onTap: () => onTap(4)),
          ],
        ),
      ),
    );
  }

  Widget _buildNavItem({required IconData icon, required String label, required bool isSelected, required VoidCallback onTap}) {
    final Color color = isSelected ? const Color(0xFF4CAF50) : Colors.grey;
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color),
          Text(label, style: TextStyle(color: color, fontSize: 12)),
        ],
      ),
    );
  }
}