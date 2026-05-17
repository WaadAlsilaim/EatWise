"""Emoji + color mapping for food items, recipes, and categories.

Used by the Flutter app to render nice placeholder images without needing
any network assets. Every food_item/recipe response carries `emoji` and
`color_hex` fields so the app can paint a consistent card.
"""
from __future__ import annotations


# Most specific match wins — order matters.
# (keyword, emoji). Keyword is lowercased substring of name_en.
SPECIFIC: list[tuple[str, str]] = [
    ("milk", "🥛"),
    ("laban", "🥛"),
    ("yogurt", "🍶"),
    ("cheese", "🧀"),
    ("egg", "🥚"),
    ("chicken", "🍗"),
    ("beef", "🥩"),
    ("meat", "🥩"),
    ("salmon", "🐟"),
    ("fish", "🐟"),
    ("tuna", "🐟"),
    ("shrimp", "🦐"),
    ("bread", "🍞"),
    ("rice", "🍚"),
    ("pasta", "🍝"),
    ("oats", "🌾"),
    ("dates", "🌴"),
    ("banana", "🍌"),
    ("apple", "🍎"),
    ("orange", "🍊"),
    ("grape", "🍇"),
    ("strawberr", "🍓"),
    ("tomato", "🍅"),
    ("cucumber", "🥒"),
    ("carrot", "🥕"),
    ("potato", "🥔"),
    ("lettuce", "🥬"),
    ("broccoli", "🥦"),
    ("onion", "🧅"),
    ("olive oil", "🫒"),
    ("sunflower oil", "🌻"),
    ("almond", "🌰"),
    ("walnut", "🌰"),
    ("peanut", "🥜"),
    ("honey", "🍯"),
    ("sugar", "🍬"),
    ("tea", "🍵"),
    ("coffee", "☕"),
    ("water", "💧"),
    ("juice", "🧃"),
    ("chocolate", "🍫"),
    ("chips", "🍟"),
    ("ketchup", "🥫"),
    ("mayonnaise", "🥫"),
    ("vinegar", "🥫"),
    ("tahini", "🥣"),
    ("fava", "🫘"),
    ("bean", "🫘"),
    ("chickpea", "🫘"),
    ("lentil", "🫘"),
    ("kabsa", "🍛"),
    ("soup", "🍲"),
    ("salad", "🥗"),
    ("sandwich", "🥪"),
    ("pizza", "🍕"),
    ("omelette", "🍳"),
    ("oatmeal", "🥣"),
    ("hummus", "🥣"),
    ("ful", "🫘"),
    ("fattoush", "🥗"),
]

# Category → (emoji fallback, color hex)
CATEGORY_STYLE: dict[str, tuple[str, str]] = {
    "dairy":     ("🥛", "#DFF5E9"),   # mint
    "protein":   ("🍗", "#FFE8D6"),   # peach
    "grain":     ("🌾", "#F5EAD2"),   # wheat
    "fruit":     ("🍎", "#FFE1EC"),   # pink
    "vegetable": ("🥦", "#E0F4D7"),   # green
    "fat":       ("🫒", "#F0ECD8"),   # olive
    "nut":       ("🌰", "#EDE0D4"),   # brown
    "sweet":     ("🍯", "#FFF3B0"),   # yellow
    "beverage":  ("🥤", "#D6EEFD"),   # blue
    "snack":     ("🍟", "#FFE3C2"),   # orange
    "condiment": ("🧂", "#EDECE8"),   # neutral
}

DEFAULT_STYLE = ("🍽️", "#F2F2F2")


def _pick_specific(name_en: str) -> str | None:
    n = (name_en or "").lower()
    for keyword, emoji in SPECIFIC:
        if keyword in n:
            return emoji
    return None


def food_visual(name_en: str, category: str | None) -> tuple[str, str]:
    """Return (emoji, color_hex) for a food item."""
    specific = _pick_specific(name_en or "")
    if specific:
        _, color = CATEGORY_STYLE.get((category or "").lower(), DEFAULT_STYLE)
        return specific, color
    return CATEGORY_STYLE.get((category or "").lower(), DEFAULT_STYLE)


def recipe_visual(title_en: str, cuisine: str | None, tags: list[str]) -> tuple[str, str]:
    """Return (emoji, color_hex) for a recipe."""
    emoji = _pick_specific(title_en) or "🍽️"
    tag_map = {
        "breakfast": ("🍳", "#FFF3B0"),
        "dinner":    ("🍽️", "#FFE8D6"),
        "salad":     ("🥗", "#E0F4D7"),
        "soup":      ("🍲", "#FFE3C2"),
        "saudi":     ("🍛", "#F5EAD2"),
        "protein_heavy": ("🍗", "#FFE8D6"),
    }
    for t in tags or []:
        if t in tag_map:
            e, color = tag_map[t]
            return (_pick_specific(title_en) or e, color)
    cuisine_colors = {
        "saudi": "#F5EAD2", "levantine": "#E0F4D7", "mediterranean": "#D6EEFD",
        "italian": "#FFE1EC", "egyptian": "#EDE0D4", "general": "#F2F2F2",
    }
    return emoji, cuisine_colors.get((cuisine or "").lower(), "#F2F2F2")
