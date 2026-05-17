"""Hand-curated real photos for each food and recipe (Unsplash direct URLs).

These are stable image URLs that render real food photos inside the app.
If a URL ever fails to load, the Flutter FoodImage widget automatically
falls back to the emoji placeholder.

To use your own photos instead:
  1. Drop JPG/PNG files into backend/storage/food-images/
  2. Point the entry below to "/storage/food-images/<filename>.jpg"
     (relative path — the backend serves it under /storage/).
"""
from __future__ import annotations


# Food items → image URL (matches food_items.name_en from init_db.py)
FOOD_IMAGES: dict[str, str] = {
    # Dairy
    "Almarai Full-Fat Milk": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&q=80",
    "Almarai Low-Fat Milk":  "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&q=80",
    "Al Rabie Laban":        "https://images.unsplash.com/photo-1628088062854-d1870b4553da?w=400&q=80",
    "Dani Yogurt":           "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&q=80",
    "White Cheese":          "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=400&q=80",

    # Protein
    "Eggs":                  "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400&q=80",
    "Chicken Breast":        "https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=400&q=80",
    "Beef":                  "https://images.unsplash.com/photo-1603048297172-c92544798d6b?w=400&q=80",
    "Salmon":                "https://images.unsplash.com/photo-1580476262798-bddd9f4b7369?w=400&q=80",
    "Canned Tuna":           "https://images.unsplash.com/photo-1606787366850-de6330128bfc?w=400&q=80",

    # Grain
    "White Bread":           "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&q=80",
    "Brown Bread":           "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=400&q=80",
    "Basmati Rice":          "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=400&q=80",
    "Pasta":                 "https://images.unsplash.com/photo-1551462147-37885acc36f1?w=400&q=80",
    "Oats":                  "https://images.unsplash.com/photo-1614961233913-a5113a4a34ed?w=400&q=80",

    # Fruits
    "Sukari Dates":          "https://images.unsplash.com/photo-1609135970970-0a1b4d68b8f3?w=400&q=80",
    "Banana":                "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&q=80",
    "Apple":                 "https://images.unsplash.com/photo-1567306301408-9b74779a11af?w=400&q=80",
    "Orange":                "https://images.unsplash.com/photo-1547514701-42782101795e?w=400&q=80",
    "Grapes":                "https://images.unsplash.com/photo-1599819811279-d5ad9cccf838?w=400&q=80",

    # Vegetables
    "Tomato":                "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400&q=80",
    "Cucumber":              "https://images.unsplash.com/photo-1604977042946-1eecc30f269e?w=400&q=80",
    "Carrot":                "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400&q=80",
    "Potato":                "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400&q=80",
    "Lettuce":               "https://images.unsplash.com/photo-1622205313162-be1d5712a43f?w=400&q=80",

    # Fats
    "Olive Oil":             "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&q=80",
    "Sunflower Oil":         "https://images.unsplash.com/photo-1474440692490-2e83ae13ba29?w=400&q=80",

    # Nuts
    "Almonds":               "https://images.unsplash.com/photo-1508736793122-f516e3ba5569?w=400&q=80",
    "Walnuts":               "https://images.unsplash.com/photo-1563418990226-a86083b1ba07?w=400&q=80",

    # Sweets / Beverages
    "Honey":                 "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400&q=80",
    "Sugar":                 "https://images.unsplash.com/photo-1600189261867-8e2e651d2ce7?w=400&q=80",
    "Tea":                   "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400&q=80",
    "Coffee":                "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&q=80",
    "Mineral Water":         "https://images.unsplash.com/photo-1523362628745-0c100150b504?w=400&q=80",
    "Orange Juice":          "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=400&q=80",
    "Chocolate":             "https://images.unsplash.com/photo-1511381939415-e44015466834?w=400&q=80",
    "Potato Chips":          "https://images.unsplash.com/photo-1613919113640-25732ec5e61f?w=400&q=80",

    # Condiments & legumes
    "Ketchup":               "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&q=80",
    "Mayonnaise":            "https://images.unsplash.com/photo-1629471722343-c14a9bb1c10b?w=400&q=80",
    "Vinegar":               "https://images.unsplash.com/photo-1624968287060-1b31cc7c9b58?w=400&q=80",
    "Tahini":                "https://images.unsplash.com/photo-1622484211148-ba58a1c60dd5?w=400&q=80",
    "Canned Fava Beans":     "https://images.unsplash.com/photo-1547496502-affa22d38842?w=400&q=80",
    "Chickpeas":             "https://images.unsplash.com/photo-1599909533881-baca76a2c4a0?w=400&q=80",
    "Lentils":               "https://images.unsplash.com/photo-1611575619293-e78e55c86ab7?w=400&q=80",
    "White Beans":           "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&q=80",
}


# Recipes → image URL (matches recipes.title_en from init_db.py)
RECIPE_IMAGES: dict[str, str] = {
    "Chicken Kabsa":                    "https://images.unsplash.com/photo-1516684732162-798a0062be99?w=500&q=80",
    "Grilled Chicken with Vegetables":  "https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=500&q=80",
    "Greek Salad":                      "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500&q=80",
    "Oats with Banana & Honey":         "https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=500&q=80",
    "Egg Omelette":                     "https://images.unsplash.com/photo-1510693206972-df098062cb71?w=500&q=80",
    "Lentil Soup":                      "https://images.unsplash.com/photo-1547592180-85f173990554?w=500&q=80",
    "Grilled Salmon":                   "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=500&q=80",
    "Pasta with Tomato Sauce":          "https://images.unsplash.com/photo-1555949258-eb67b1ef0ceb?w=500&q=80",
    "Fattoush Salad":                   "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&q=80",
    "Ful Medames":                      "https://images.unsplash.com/photo-1604152135912-04a022e23696?w=500&q=80",
    "Hummus":                           "https://images.unsplash.com/photo-1577805947697-89e18249d767?w=500&q=80",
    "Chicken Soup":                     "https://images.unsplash.com/photo-1547308283-b941cf66bc78?w=500&q=80",
    # Fruit-based recipes
    "Apple Cinnamon Oats":              "https://images.unsplash.com/photo-1571748982800-fa51082c2224?w=500&q=80",
    "Fresh Fruit Salad":                "https://images.unsplash.com/photo-1490474418585-ba9bad8fd0ea?w=500&q=80",
    "Fresh Orange Juice":               "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=500&q=80",
    "Banana Apple Yogurt Bowl":         "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=500&q=80",
    "Orange Banana Smoothie":           "https://images.unsplash.com/photo-1638176067051-99eda4f0fcc4?w=500&q=80",
}


def food_image_url(name_en: str) -> str:
    """Return a direct image URL for a food item, or empty string if none."""
    return FOOD_IMAGES.get(name_en, "")


def recipe_image_url(title_en: str) -> str:
    """Return a direct image URL for a recipe, or empty string if none."""
    return RECIPE_IMAGES.get(title_en, "")
