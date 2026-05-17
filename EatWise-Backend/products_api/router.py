"""Flutter-compatible /api/products/products/ endpoint.

The Flutter ProductsScreen reads a flat list of objects with these fields:
    id, name, calories, protein, carbs, fat, category
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core import models
from app.core.database import get_db
from app.core.visuals import food_visual
from app.core.images_map import food_image_url


router = APIRouter(prefix="/products", tags=["Products (Flutter)"])


@router.get("/products/")
def list_products(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return a flat list of food items in the shape the Flutter app expects."""
    rows = (db.query(models.FoodItem)
              .filter(models.FoodItem.is_active == True)
              .limit(limit).all())

    result = []
    for f in rows:
        n = f.nutrition
        emoji, color = food_visual(f.name_en, f.category)
        # Prefer explicit image_path on the row (if an admin uploaded one),
        # else fall back to our curated Unsplash URL map.
        if f.image_path and f.image_path.strip():
            img = f.image_path
        else:
            img = food_image_url(f.name_en)
        result.append({
            "id": f.id,
            "name": f.name_en,
            "name_ar": f.name_ar,
            "category": f.category or "",
            "brand": f.brand or "",
            "emoji": emoji,
            "color_hex": color,
            "image_url": img,
            "calories": int(float(n.kcal)) if n else 0,
            "protein": float(n.protein_g) if n else 0.0,
            "carbs": float(n.carbs_g) if n else 0.0,
            "fat": float(n.fat_g) if n else 0.0,
            "sugar": float(n.sugar_g or 0) if n else 0.0,
            "fiber": float(n.fiber_g or 0) if n else 0.0,
            "sodium": float(n.sodium_mg or 0) if n else 0.0,
        })
    return result
