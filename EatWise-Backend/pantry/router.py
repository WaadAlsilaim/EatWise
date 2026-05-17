"""Flutter-compatible /api/pantry/ endpoints.

The Pantry is the user's personal "My Products" list. Items can be added:
  • manually from the catalog (POST /api/pantry/)
  • automatically from image analysis (called by /analyze-image)

Routes (all auth):
  GET    /api/pantry/              → list current pantry
  POST   /api/pantry/              → add a food by id (or upsert quantity)
  POST   /api/pantry/bulk/         → add many at once (used by image analysis)
  PATCH  /api/pantry/{food_id}/    → update quantity
  DELETE /api/pantry/{food_id}/    → remove a single item
  DELETE /api/pantry/              → clear the entire pantry
"""
from datetime import datetime
from typing import Iterable

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core import models, security
from app.core.database import get_db
from app.core.errors import err_invalid_request, err_not_found, err_unauthorized
from app.core.visuals import food_visual
from app.core.images_map import food_image_url


router = APIRouter(prefix="/pantry", tags=["Pantry (Flutter)"])


def _try_user(authorization: str | None, db: Session) -> models.User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    payload = security.decode_access_token(token)
    if not payload:
        return None
    try:
        uid = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        return None
    return db.query(models.User).filter(
        models.User.id == uid, models.User.is_active == True
    ).first()


def _serialize(p: models.PantryItem) -> dict:
    f = p.food
    if not f:
        return {
            "id": p.id, "food_id": p.food_id,
            "name": "(unknown)", "name_ar": "", "category": "",
            "quantity": float(p.quantity), "unit": p.unit,
            "source": p.source, "added_at": p.added_at.isoformat(),
            "emoji": "🍽️", "color_hex": "#F2F2F2", "image_url": "",
            "calories": 0, "protein": 0.0, "carbs": 0.0, "fat": 0.0,
        }
    n = f.nutrition
    emoji, color = food_visual(f.name_en, f.category)
    img = (f.image_path or "").strip() or food_image_url(f.name_en)
    return {
        "id": p.id,
        "food_id": f.id,
        "name": f.name_en,
        "name_ar": f.name_ar,
        "category": f.category or "",
        "quantity": float(p.quantity),
        "unit": p.unit,
        "source": p.source,
        "added_at": p.added_at.isoformat(),
        "emoji": emoji,
        "color_hex": color,
        "image_url": img,
        "calories": int(float(n.kcal)) if n else 0,
        "protein": float(n.protein_g) if n else 0.0,
        "carbs": float(n.carbs_g) if n else 0.0,
        "fat": float(n.fat_g) if n else 0.0,
    }


# ============================================================
# Internal helper used by analyze-image to push detected items in
# ============================================================
def add_foods_to_pantry(
    db: Session, user_id: int, food_ids: Iterable[int],
    source: str = "scan",
) -> int:
    """Upsert food_ids into the user's pantry. Returns number of new rows added."""
    added = 0
    for fid in set(food_ids):
        existing = db.query(models.PantryItem).filter(
            models.PantryItem.user_id == user_id,
            models.PantryItem.food_id == fid,
        ).first()
        if existing:
            existing.added_at = datetime.utcnow()
            existing.source = source
        else:
            db.add(models.PantryItem(
                user_id=user_id, food_id=fid,
                quantity=1, unit="piece", source=source,
            ))
            added += 1
    db.commit()
    return added


# ============================================================
# Routes
# ============================================================
@router.get("/")
def list_pantry(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (db.query(models.PantryItem)
              .filter(models.PantryItem.user_id == user.id)
              .order_by(desc(models.PantryItem.added_at))
              .all())
    return [_serialize(p) for p in rows]


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_to_pantry(
    body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food_id = body.get("food_id")
    quantity = float(body.get("quantity") or 1)
    unit = str(body.get("unit") or "piece")
    if not food_id:
        raise err_invalid_request("food_id is required")
    food = db.query(models.FoodItem).filter(models.FoodItem.id == food_id).first()
    if not food:
        raise err_not_found("Food not found")

    existing = db.query(models.PantryItem).filter(
        models.PantryItem.user_id == user.id,
        models.PantryItem.food_id == food_id,
    ).first()
    if existing:
        existing.quantity = quantity
        existing.unit = unit
        existing.added_at = datetime.utcnow()
        existing.source = "manual"
        db.commit()
        db.refresh(existing)
        return _serialize(existing)

    item = models.PantryItem(
        user_id=user.id, food_id=food_id,
        quantity=quantity, unit=unit, source="manual",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize(item)


@router.post("/bulk/", status_code=status.HTTP_201_CREATED)
def add_bulk(
    body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Used by automation (e.g., from an image-analysis pipeline)."""
    ids = body.get("food_ids") or []
    source = str(body.get("source") or "scan")
    if not isinstance(ids, list):
        raise err_invalid_request("food_ids must be a list of integers")
    added = add_foods_to_pantry(db, user.id, [int(x) for x in ids], source=source)
    return {"added": added, "total_requested": len(ids)}


@router.patch("/{food_id}/")
def update_item(
    food_id: int,
    body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.query(models.PantryItem).filter(
        models.PantryItem.user_id == user.id,
        models.PantryItem.food_id == food_id,
    ).first()
    if not p:
        raise err_not_found("Item not found in pantry")
    if "quantity" in body and body["quantity"] is not None:
        try:
            p.quantity = float(body["quantity"])
        except (TypeError, ValueError):
            pass
    if "unit" in body and body["unit"]:
        p.unit = str(body["unit"])
    p.added_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return _serialize(p)


@router.delete("/{food_id}/", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(
    food_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = db.query(models.PantryItem).filter(
        models.PantryItem.user_id == user.id,
        models.PantryItem.food_id == food_id,
    ).delete()
    db.commit()
    if not deleted:
        raise err_not_found("Item not in pantry")
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_pantry(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.PantryItem).filter(
        models.PantryItem.user_id == user.id
    ).delete()
    db.commit()
    return None
