class ProductModel {
  final String name;
  final int id;
  final String details;
  final String imageUrl;
  final List<String> ingredients;
  final String emoji;
  final String colorHex;
  bool isSelected;

  ProductModel({
    required this.id,
    required this.name,
    required this.details,
    required this.imageUrl,
    required this.ingredients,
    this.emoji = '🍽️',
    this.colorHex = '#F2F2F2',
    this.isSelected = false,
  });
}
