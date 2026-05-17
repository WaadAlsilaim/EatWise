"""
Real image analysis with YOLOv8n trained on Open Images V7 (601 classes).

Why Open Images V7 instead of the default COCO model:
  COCO has only 10 food classes (apple, banana, orange, broccoli, carrot,
  pizza, sandwich, hot dog, donut, cake) — can't detect eggs, bread, milk,
  cheese, chicken, fish, etc.

  Open Images V7 has ~60 food-related classes, including:
    egg, milk, cheese, bread, pastry, bagel, pancake, waffle, muffin,
    croissant, cookie, ice cream, sushi, hamburger, taco, burrito,
    french fries, chicken, fish, shrimp, lobster, crab, cucumber, tomato,
    potato, cabbage, cauliflower, mushroom, lemon, mango, pineapple,
    watermelon, grape, peach, pear, strawberry, coffee, tea, juice, wine,
    salad, pasta, dessert, candy, honeycomb, etc.

If `ultralytics` is not installed, everything degrades gracefully.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core import models
from app.ai import clip_classifier


# ---- Model loading (singleton) --------------------------------------------
_YOLO = None
_LOAD_ERR: str | None = None
_LOADED_MODEL_NAME: str | None = None

# Default model name. Override with EATWISE_YOLO_MODEL env var if needed.
#   • "yolov8n-oiv7.pt" — 601 classes, Open Images V7 (RECOMMENDED)
#   • "yolov8n.pt"      — 80 classes, COCO (only 10 foods)
DEFAULT_MODEL = "yolov8n-oiv7.pt"


def _load_model():
    """Load the YOLO model on first use. ~6 MB, auto-downloads once to ~/.cache/ultralytics."""
    global _YOLO, _LOAD_ERR, _LOADED_MODEL_NAME
    if _YOLO is not None or _LOAD_ERR:
        return _YOLO
    try:
        from ultralytics import YOLO  # type: ignore
        model_name = os.getenv("EATWISE_YOLO_MODEL", DEFAULT_MODEL)
        _YOLO = YOLO(model_name)
        _LOADED_MODEL_NAME = model_name
        return _YOLO
    except Exception as e:  # pragma: no cover
        _LOAD_ERR = str(e)
        return None


def is_available() -> bool:
    """Quick check for the router — does not trigger a full model load."""
    try:
        import ultralytics  # noqa: F401
        return True
    except ImportError:
        return False


# ---- YOLO class → food_items mapping ---------------------------------------
# Keys are lowercase class names as emitted by the YOLO model.
# Values are candidate name_en entries in our DB, tried in order.
#
# We combine COCO + Open Images V7 class names so the mapping works for
# either model. Extra synonyms are included to improve match rate.
FOOD_MAP: dict[str, list[str]] = {
    # ============ Fruits ============
    "apple":            ["Apple"],
    "banana":           ["Banana"],
    "orange":           ["Orange", "Orange Juice"],
    "grape":            ["Grapes"],
    "grapefruit":       ["Orange", "Grapes"],
    "lemon":            ["Orange"],                  # closest in our DB
    "strawberry":       ["Strawberry", "Apple"],     # fallback to apple
    "peach":            ["Peach", "Apple"],
    "pear":             ["Pear", "Apple"],
    "mango":            ["Mango", "Banana"],
    "pineapple":        ["Pineapple", "Banana"],
    "watermelon":       ["Watermelon", "Apple"],
    "cantaloupe":       ["Cantaloupe", "Apple"],
    "pomegranate":      ["Pomegranate", "Apple"],
    "coconut":          ["Coconut", "Almonds"],
    "common fig":       ["Sukari Dates"],
    "fruit":            ["Apple"],

    # ============ Vegetables ============
    "tomato":           ["Tomato"],
    "cucumber":         ["Cucumber"],
    "carrot":           ["Carrot"],
    "potato":           ["Potato"],
    "broccoli":         ["Broccoli"],
    "cauliflower":      ["Cauliflower", "Broccoli"],
    "cabbage":          ["Cabbage", "Lettuce"],
    "lettuce":          ["Lettuce"],
    "mushroom":         ["Mushroom", "Broccoli"],
    "radish":           ["Radish", "Carrot"],
    "pumpkin":          ["Pumpkin", "Potato"],
    "zucchini":         ["Zucchini", "Cucumber"],
    "bell pepper":      ["Bell Pepper", "Tomato"],
    "squash":           ["Pumpkin", "Potato"],
    "squash (plant)":   ["Pumpkin", "Potato"],
    "asparagus":        ["Asparagus", "Broccoli"],
    "garden asparagus": ["Asparagus", "Broccoli"],
    "artichoke":        ["Artichoke", "Broccoli"],
    "vegetable":        ["Carrot"],

    # ============ Bread / Grains / Pastries ============
    "bread":            ["White Bread", "Brown Bread"],
    "bagel":            ["White Bread", "Brown Bread"],
    "croissant":        ["White Bread"],
    "pastry":           ["White Bread"],
    "pretzel":          ["White Bread"],
    "baked goods":      ["White Bread"],
    "muffin":           ["White Bread", "Cake"],
    "pancake":          ["White Bread"],
    "waffle":           ["White Bread"],
    "pasta":            ["Pasta"],
    "noodle":           ["Pasta"],
    "rice":             ["Basmati Rice"],

    # ============ Dairy & Eggs ============
    "egg (food)":       ["Eggs"],
    "egg":              ["Eggs"],
    "eggs":             ["Eggs"],
    "fried egg":        ["Eggs"],
    "boiled egg":       ["Eggs"],
    "scrambled egg":    ["Eggs"],
    "egg yolk":         ["Eggs"],
    "milk":             ["Almarai Low-Fat Milk", "Almarai Full-Fat Milk"],
    "cheese":           ["White Cheese"],
    "yogurt":           ["Dani Yogurt", "Al Rabie Laban"],
    "dairy product":    ["Dani Yogurt", "Al Rabie Laban", "Almarai Full-Fat Milk"],
    "cream":            ["Dani Yogurt"],

    # ============ Meat / Poultry / Seafood ============
    "chicken":          ["Chicken Breast"],
    "turkey":           ["Chicken Breast"],
    "fish":             ["Salmon", "Canned Tuna"],
    "shrimp":           ["Shrimp", "Salmon"],
    "crab":             ["Crab", "Salmon"],
    "lobster":          ["Lobster", "Salmon"],
    "oyster":           ["Oyster", "Salmon"],
    "squid":            ["Squid", "Salmon"],
    "shellfish":        ["Shrimp", "Salmon"],
    "seafood":          ["Salmon", "Canned Tuna"],
    "sushi":            ["Sushi", "Salmon"],

    # ============ Prepared foods & fast food ============
    "pizza":            ["Pizza"],
    "sandwich":         ["Sandwich", "White Bread"],
    "submarine sandwich": ["Sandwich", "White Bread"],
    "hamburger":        ["Hamburger", "Sandwich"],
    "burrito":          ["Burrito", "Sandwich"],
    "taco":             ["Taco", "Sandwich"],
    "hot dog":          ["Hot Dog"],
    "french fries":     ["French Fries", "Potato Chips", "Potato"],
    "salad":            ["Greek Salad", "Fattoush Salad"],
    "fast food":        ["Sandwich"],
    "snack":            ["Potato Chips"],

    # ============ Sweets ============
    "donut":            ["Donut", "Chocolate"],
    "doughnut":         ["Donut", "Chocolate"],
    "cake":             ["Cake", "Chocolate"],
    "cookie":           ["Cookie", "Chocolate"],
    "candy":            ["Chocolate", "Sugar"],
    "ice cream":        ["Ice Cream", "Chocolate"],
    "dessert":          ["Cake", "Chocolate"],
    "tart":             ["Cake"],
    "honeycomb":        ["Honey"],
    "popcorn":          ["Popcorn", "Potato Chips"],

    # ============ Beverages ============
    "bottle":           ["Mineral Water", "Almarai Low-Fat Milk", "Orange Juice"],
    "cup":              ["Tea", "Coffee"],
    "mug":              ["Tea", "Coffee"],
    "coffee":           ["Coffee"],
    "coffee cup":       ["Coffee"],
    "tea":              ["Tea"],
    "teapot":           ["Tea"],
    "kettle":           ["Tea"],
    "juice":            ["Orange Juice"],
    "wine glass":       ["Orange Juice"],
    "wine":             ["Orange Juice"],
    "beer":             ["Mineral Water"],
    "cocktail":         ["Orange Juice"],
    "drink":            ["Orange Juice", "Mineral Water"],

    # ============ Containers (generic guess) ============
    "bowl":             ["Lentil Soup", "Chicken Soup", "Greek Salad"],
    "plate":            ["Greek Salad"],
    "food":             ["Sandwich"],
}


def _find_food(db: Session, candidates: list[str]) -> models.FoodItem | None:
    """Return the first matching FoodItem for any of the candidate names."""
    for name in candidates:
        f = (db.query(models.FoodItem)
               .filter(models.FoodItem.name_en.ilike(name))
               .first())
        if f:
            return f
    return None


def _nutrition_dict(f: models.FoodItem) -> dict[str, float]:
    n = f.nutrition
    if not n:
        return {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    return {
        "kcal": float(n.kcal),
        "protein": float(n.protein_g),
        "carbs": float(n.carbs_g),
        "fat": float(n.fat_g),
    }


def detect_from_file(image_path: Path, db: Session,
                     yolo_threshold: float = 0.10,   # let YOLO emit even weak guesses
                     final_threshold: float = 0.25,  # we filter AFTER color disambiguation
                     min_accept_conf: float = 0.40,  # below this, flag as low_confidence
                     max_items: int = 10) -> dict[str, Any]:
    """
    Run YOLO on the image file and return structured detection results.

    Response:
      {
        "available": True,
        "model": "yolov8n-oiv7.pt",
        "detected_items": [
          {"label": "egg (food)", "confidence": 0.88, "food_id": 6,
           "food_name_en": "Eggs", "food_name_ar": "بيض",
           "nutrition": {...}},
          ...
        ],
        "totals": {"kcal": ..., "protein": ..., "carbs": ..., "fat": ...},
        "raw_classes": [...]
      }
    """
    if not is_available():
        return {
            "available": False,
            "detected_items": [],
            "totals": {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0},
            "raw_classes": [],
            "note": "Install ultralytics to enable real detection: pip install ultralytics",
        }

    model = _load_model()
    if model is None:
        return {
            "available": False,
            "detected_items": [],
            "totals": {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0},
            "raw_classes": [],
            "note": f"Model load failed: {_LOAD_ERR}",
        }

    # Pass 1: ask YOLO for ALL detections, even weak ones (conf >= yolo_threshold).
    # We filter for real after running color disambiguation, because YOLO
    # often labels an orange as "apple" at ~0.20 conf — once color confirms
    # it's actually orange, we boost it above final_threshold.
    results = model.predict(
        source=str(image_path),
        conf=yolo_threshold,
        verbose=False,
        imgsz=640,
    )

    raw_classes: list[str] = []
    best_per_class: dict[str, float] = {}
    for r in results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            cls_idx = int(box.cls[0].item())
            label = r.names.get(cls_idx, str(cls_idx)).lower().strip()
            confidence = float(box.conf[0].item())
            raw_classes.append(label)
            if label not in best_per_class or confidence > best_per_class[label]:
                best_per_class[label] = confidence

    # ---- Color-based disambiguation for confusable fruits -----------------
    # Runs whenever the top class is in the "easily confused" group OR when
    # YOLO returned nothing useful but the photo has an unambiguous fruit
    # color (a clean orange on a white background, for example).
    best_per_class = _color_disambiguate(image_path, best_per_class)

    detected_items: list[dict[str, Any]] = []
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    seen_food_ids: set[int] = set()
    low_confidence = False
    clip_used = False
    clip_top_score: float | None = None

    # ---- Find YOLO's best confident food match -----------------------------
    yolo_best_food = None
    yolo_best_conf = 0.0
    for label, confidence in sorted(best_per_class.items(), key=lambda x: -x[1]):
        if label in FOOD_MAP:
            food = _find_food(db, FOOD_MAP[label])
            if food:
                yolo_best_food = (label, confidence, food)
                yolo_best_conf = confidence
                break

    # ---- CLIP pass: when YOLO is uncertain, ask CLIP for its opinion -------
    # CLIP is a smarter zero-shot classifier; it understands the image content
    # and returns the closest food from our DB by semantic similarity.
    if yolo_best_conf < 0.55 and clip_classifier.is_available():
        clip_match = clip_classifier.best_match(image_path, db)
        if clip_match:
            clip_used = True
            clip_top_score = clip_match["similarity"]
            # Decision rule:
            #   • CLIP very confident (>= CLIP_DOMINATE) → CLIP wins
            #   • CLIP confident (>= CLIP_ACCEPT) AND YOLO weak → CLIP wins
            #   • Otherwise → YOLO wins (or whoever found something)
            clip_strong = clip_match["similarity"] >= clip_classifier.CLIP_DOMINATE
            clip_decent = clip_match["similarity"] >= clip_classifier.CLIP_ACCEPT
            if clip_strong or (clip_decent and yolo_best_conf < 0.40):
                # Use CLIP's match as the primary detection
                food = db.query(models.FoodItem).filter(
                    models.FoodItem.id == clip_match["food_id"]
                ).first()
                if food:
                    n = _nutrition_dict(food)
                    confidence_for_ui = max(clip_match["similarity"] * 1.5, 0.55)
                    confidence_for_ui = min(confidence_for_ui, 0.99)
                    detected_items.append({
                        "label": food.name_en.lower(),
                        "confidence": round(confidence_for_ui, 3),
                        "low_confidence": confidence_for_ui < min_accept_conf,
                        "food_id": food.id,
                        "food_name_en": food.name_en,
                        "food_name_ar": food.name_ar,
                        "category": food.category,
                        "source": "clip",
                        "clip_similarity": round(clip_match["similarity"], 3),
                        "nutrition": n,
                    })
                    seen_food_ids.add(food.id)
                    for k in totals:
                        totals[k] += n[k] * 1.5

    # ---- Walk YOLO predictions (skip ones already covered by CLIP) ---------
    for label, confidence in sorted(best_per_class.items(), key=lambda x: -x[1]):
        if confidence < final_threshold:
            continue
        if label not in FOOD_MAP:
            continue
        food = _find_food(db, FOOD_MAP[label])
        if not food or food.id in seen_food_ids:
            continue
        seen_food_ids.add(food.id)

        n = _nutrition_dict(food)
        if confidence < min_accept_conf:
            low_confidence = True

        detected_items.append({
            "label": label,
            "confidence": round(confidence, 3),
            "low_confidence": confidence < min_accept_conf,
            "food_id": food.id,
            "food_name_en": food.name_en,
            "food_name_ar": food.name_ar,
            "category": food.category,
            "source": "yolo",
            "nutrition": n,
        })
        for k in totals:
            totals[k] += n[k] * 1.5
        if len(detected_items) >= max_items:
            break

    return {
        "available": True,
        "model": _LOADED_MODEL_NAME or DEFAULT_MODEL,
        "detected_items": detected_items,
        "totals": {k: round(v, 1) for k, v in totals.items()},
        "raw_classes": raw_classes,
        "any_low_confidence": low_confidence,
        "clip_used": clip_used,
        "clip_top_similarity": clip_top_score,
    }


# ---------------------------------------------------------------------------
# Color disambiguation — fixes "orange labelled as apple" misclassifications
# ---------------------------------------------------------------------------
def _dominant_color(image_path: Path) -> tuple[int, int, int] | None:
    """Return the median (R, G, B) of the image, or None if PIL/numpy fail."""
    try:
        from PIL import Image
        import numpy as np
        with Image.open(image_path) as im:
            im = im.convert("RGB").resize((64, 64))
            arr = np.array(im)
            # Median is more robust than mean against backgrounds
            r = int(np.median(arr[:, :, 0]))
            g = int(np.median(arr[:, :, 1]))
            b = int(np.median(arr[:, :, 2]))
            return r, g, b
    except Exception:
        return None


_FRUIT_LIKE_HINTS = {
    "apple", "orange", "peach", "tomato", "pear", "lemon",
    "fruit", "common fig", "vegetable", "food",
}


def _classify_color(rgb: tuple[int, int, int]) -> str | None:
    """Return a fruit label if the RGB sample is unambiguous, else None."""
    r, g, b = rgb
    if r > 200 and 100 < g < 180 and b < 120:        return "orange"
    if r > 180 and g < 60 and b < 60:                return "tomato"
    if r > 180 and g < 90 and b < 90:                return "apple"   # red apple
    if r < 200 and g > 180 and b < 150:              return "apple"   # green apple
    if r > 230 and g > 220 and b < 160:              return "lemon"
    return None


def _color_disambiguate(image_path: Path,
                        best_per_class: dict[str, float]
                        ) -> dict[str, float]:
    """Use the image's dominant color to fix or rescue fruit detections.

    Three modes:
      A. YOLO got nothing useful → if color is unambiguous, INJECT a label
         at confidence 0.55. (Rescues clean orange-on-white photos.)
      B. YOLO returned a confusable-fruit class with low/medium confidence
         and color disagrees → SWAP the label.
      C. YOLO is highly confident (>= 0.55) → trust it, don't second-guess.
    """
    rgb = _dominant_color(image_path)
    color_guess = _classify_color(rgb) if rgb else None

    if not best_per_class:
        # Mode A: nothing from YOLO — give the color heuristic a chance
        if color_guess:
            return {color_guess: 0.55}
        return best_per_class

    top_label, top_conf = max(best_per_class.items(), key=lambda x: x[1])

    # Mode A2: YOLO saw only generic/weak hints — color may rescue
    if top_conf < 0.55 and top_label not in _FRUIT_LIKE_HINTS:
        # Top class isn't even a fruit-looking thing — color guess may add a fruit
        if color_guess:
            out = dict(best_per_class)
            out[color_guess] = max(out.get(color_guess, 0.0), 0.55)
            return out
        return best_per_class

    if top_conf >= 0.55:
        return best_per_class  # high confidence — trust YOLO

    if color_guess and color_guess != top_label:
        out = dict(best_per_class)
        out[top_label] = top_conf * 0.5         # demote wrong guess
        out[color_guess] = max(out.get(color_guess, 0.0), top_conf + 0.20)
        return out

    return best_per_class
