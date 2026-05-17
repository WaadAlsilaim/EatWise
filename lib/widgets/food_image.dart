import 'package:flutter/material.dart';

/// A reusable "image" widget that renders either:
///  • a network image if [imageUrl] is a non-empty http(s) URL, or
///  • a colored square with a large emoji (fast, offline, always pretty).
///
/// Usage:
///   FoodImage(
///     emoji: item['emoji'],
///     colorHex: item['color_hex'],
///     imageUrl: item['image_url'],
///     size: 64,
///   )
class FoodImage extends StatelessWidget {
  final String? emoji;
  final String? colorHex;
  final String? imageUrl;
  final double size;
  final double borderRadius;

  const FoodImage({
    super.key,
    this.emoji,
    this.colorHex,
    this.imageUrl,
    this.size = 56,
    this.borderRadius = 16,
  });

  Color _parseColor(String? hex) {
    if (hex == null || hex.isEmpty) return const Color(0xFFF2F2F2);
    var h = hex.replaceAll('#', '').trim();
    if (h.length == 6) h = 'FF$h';
    try {
      return Color(int.parse(h, radix: 16));
    } catch (_) {
      return const Color(0xFFF2F2F2);
    }
  }

  bool get _hasNetworkImage =>
      imageUrl != null &&
      imageUrl!.isNotEmpty &&
      (imageUrl!.startsWith('http://') || imageUrl!.startsWith('https://'));

  @override
  Widget build(BuildContext context) {
    if (_hasNetworkImage) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: Image.network(
          imageUrl!,
          width: size,
          height: size,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => _buildEmojiBox(),
          loadingBuilder: (_, child, progress) {
            if (progress == null) return child;
            return _buildEmojiBox();
          },
        ),
      );
    }
    return _buildEmojiBox();
  }

  Widget _buildEmojiBox() {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: _parseColor(colorHex),
        borderRadius: BorderRadius.circular(borderRadius),
      ),
      alignment: Alignment.center,
      child: Text(
        emoji ?? '🍽️',
        style: TextStyle(fontSize: size * 0.55),
        textAlign: TextAlign.center,
      ),
    );
  }
}
