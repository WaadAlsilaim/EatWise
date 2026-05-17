"""Basket utilities: nutrition summary + stub CV/OCR pipeline.

The real YOLO + OCR pipeline belongs in app/ai/. For the prototype, we implement
a deterministic stub that simulates processing time and returns no auto-detected
items; users add items manually via the /items endpoints. Swap this for the real
pipeline once the YOLO model is trained.
"""
from datetime import datetime
from sqlalchemy.orm import Session

from app.core import models


def compute_summary(basket: models.Basket) -> dict:
    totals = {"kcal": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0,
             "sugar_g": 0.0, "fiber_g": 0.0, "sodium_mg": 0.0}
    for item in basket.items:
        if not item.food or not item.food.nutrition:
            continue
        n = item.food.nutrition
        factor = float(item.quantity) * 1.0  # assume 1 unit = per_amount for now
        totals["kcal"] += float(n.kcal) * factor
        totals["protein_g"] += float(n.protein_g) * factor
        totals["carbs_g"] += float(n.carbs_g) * factor
        totals["fat_g"] += float(n.fat_g) * factor
        totals["sugar_g"] += float(n.sugar_g or 0) * factor
        totals["fiber_g"] += float(n.fiber_g or 0) * factor
        totals["sodium_mg"] += float(n.sodium_mg or 0) * factor
    return {k: round(v, 2) for k, v in totals.items()}


def detect_alerts(db: Session, user: models.User, basket: models.Basket) -> list[dict]:
    """Compare basket items against the user's allergens; return alert payloads."""
    alerts = []
    user_allergen_slugs = {ua.allergen.slug for ua in user.allergens}
    if not user_allergen_slugs:
        return alerts

    for item in basket.items:
        if not item.food:
            continue
        # naive slug match on category/name_en for demo
        name = (item.food.name_en or "").lower()
        category = (item.food.category or "").lower()
        triggers = []
        if "milk" in name or "yogurt" in name or "cheese" in name or category == "dairy":
            if "lactose" in user_allergen_slugs or "milk" in user_allergen_slugs:
                triggers.append("milk/lactose")
        if "bread" in name or "wheat" in name or "flour" in name:
            if "gluten" in user_allergen_slugs:
                triggers.append("gluten")
        if "peanut" in name or "nut" in name:
            if "peanut" in user_allergen_slugs or "tree_nut" in user_allergen_slugs:
                triggers.append("nuts")
        if triggers:
            alerts.append({
                "kind": "allergen",
                "title": f"Allergen warning: {item.food.name_en}",
                "body": f"Contains {', '.join(triggers)} which you marked as an allergen.",
                "food_id": item.food.id,
            })
    return alerts


def process_basket(db: Session, basket_id: int) -> None:
    """
    Synchronous stub: mark basket as ready. When the real CV/OCR pipeline is
    ready, insert detected items here.
    """
    basket = db.query(models.Basket).filter(models.Basket.id == basket_id).first()
    if not basket:
        return
    basket.status = "ready"
    basket.processed_at = datetime.utcnow()
    db.commit()
