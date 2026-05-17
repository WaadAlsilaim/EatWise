"""Flutter-compatible /analyze-image endpoint with REAL AI image analysis.

Pipeline:
  1. Save the uploaded image under storage/baskets/.
  2. Run YOLOv8n (COCO) via app.ai.detector → get list of detected food items.
  3. Each detected item is mapped to a real food_items row in our DB.
  4. Return a FoodModel-compatible response that also includes a richer
     `detected_items` array the app can render.

If `ultralytics` is not installed (or fails to load), we fall back to the
deterministic allergen-safe stub so the endpoint never breaks.
"""
import json
import random
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, UploadFile
from sqlalchemy.orm import Session

from app.ai import detector
from app.core import models, security
from app.core.config import settings
from app.core.database import get_db
from app.pantry.router import add_foods_to_pantry


router = APIRouter(tags=["Analyze (Flutter)"])


def _try_current_user(authorization: str | None, db: Session) -> models.User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    payload = security.decode_access_token(token)
    if not payload:
        return None
    try:
        user_id = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()


def _fallback_recipe(db: Session, user: models.User | None) -> dict:
    """Returned when YOLO could not detect any food in the image.

    IMPORTANT: We deliberately return ZERO nutrition (instead of fake numbers
    like 450 kcal) because making up values would mislead the user. The
    Flutter UI checks `ai_status` and shows a clear "Nothing detected" message
    with guidance instead of pretending we found a meal.
    """
    return {
        "name": "Nothing recognized",
        "recipe_name": "Nothing recognized",
        "calories": 0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "meal_type": "unknown",
        "instructions": (
            "We couldn't recognize any food in this photo. "
            "Try a closer, well-lit shot of a single item, or add the item "
            "manually from My Products → +."
        ),
    }


def _summary_name(items: list[dict]) -> str:
    if not items:
        return "Analysis result"
    if len(items) == 1:
        return items[0]["food_name_en"]
    names = [it["food_name_en"] for it in items[:3]]
    if len(items) > 3:
        return ", ".join(names) + f" +{len(items)-3} more"
    return ", ".join(names)


@router.post("/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    """
    Accept an uploaded image, run real YOLO-based detection, and return the
    aggregated result plus per-item breakdown.

    Response shape is backward-compatible with food_service.dart's FoodModel
    plus an extra `detected_items` array for richer UIs.
    """
    # 1. Save the image
    data = await image.read()
    ext = ".jpg"
    ct = (image.content_type or "").lower()
    if "png" in ct:
        ext = ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    storage_root = Path(settings.storage_dir) / "baskets"
    storage_root.mkdir(parents=True, exist_ok=True)
    fpath = storage_root / filename
    fpath.write_bytes(data)
    image_url = f"/storage/baskets/{filename}"

    user = _try_current_user(authorization, db)

    # 2. Run AI detection
    result = detector.detect_from_file(fpath, db)

    if not result["available"] or not result["detected_items"]:
        # Either AI is disabled, or it saw nothing it recognizes — fall back.
        fallback = _fallback_recipe(db, user)
        fallback["image_url"] = image_url
        fallback["detected_items"] = []
        fallback["ai_status"] = "unavailable" if not result["available"] else "no_detections"
        fallback["ai_note"] = result.get("note", "")
        fallback["raw_classes"] = result.get("raw_classes", [])
        # Diagnostic info — helps the user figure out why nothing matched.
        fallback["model"] = result.get("model", "unknown")
        # Print so it appears in the backend console too
        print(f"\n[ANALYZE] model={fallback['model']} raw_classes={fallback['raw_classes']}\n",
              flush=True)
        return fallback

    # 3. Build the aggregate response
    items = result["detected_items"]
    totals = result["totals"]

    # Create readable instructions from the detected items
    lines = ["Detected in your photo:"]
    for it in items:
        lines.append(
            f"• {it['food_name_en']} ({it['food_name_ar']}) — "
            f"{it['nutrition']['kcal']:.0f} kcal / 100g "
            f"(confidence {it['confidence']*100:.0f}%)"
        )
    instructions = "\n".join(lines)

    # Check for allergy conflicts (best-effort)
    allergy_warnings: list[str] = []
    if user:
        ap = db.query(models.AccountProfile).filter(
            models.AccountProfile.user_id == user.id
        ).first()
        if ap and ap.allergies and ap.allergies != "None":
            user_allergens = [a.strip().lower() for a in ap.allergies.split(",") if a.strip()]
            keyword_map = {
                "dairy": ["milk", "yogurt", "cheese", "laban"],
                "peanuts": ["peanut"],
                "gluten": ["bread", "wheat", "flour", "pasta", "sandwich"],
                "shellfish": ["shrimp", "prawn", "crab"],
                "soy": ["soy"], "eggs": ["egg"],
                "tree nuts": ["almond", "walnut", "nut"],
            }
            for a in user_allergens:
                for aname, kws in keyword_map.items():
                    if aname not in a:
                        continue
                    for it in items:
                        nm = it["food_name_en"].lower()
                        if any(kw in nm for kw in kws):
                            allergy_warnings.append(
                                f"⚠ {it['food_name_en']} may contain {aname}"
                            )

    # Auto-add detected items to the user's pantry (only when authenticated)
    pantry_added = 0
    if user:
        food_ids = [it["food_id"] for it in items if it.get("food_id")]
        if food_ids:
            try:
                pantry_added = add_foods_to_pantry(
                    db, user.id, food_ids, source="scan"
                )
            except Exception:
                pantry_added = 0

    return {
        "name": _summary_name(items),
        "recipe_name": _summary_name(items),
        "calories": int(totals["kcal"]),
        "protein": round(totals["protein"], 1),
        "carbs": round(totals["carbs"], 1),
        "fat": round(totals["fat"], 1),
        "meal_type": "detected",
        "image_url": image_url,
        "instructions": instructions,
        # Richer payload (Flutter can read or ignore these):
        "ai_status": "ok",
        "detected_items": items,
        "raw_classes": result["raw_classes"],
        "allergy_warnings": allergy_warnings,
        # Pantry integration:
        "pantry_added_count": pantry_added,
        "pantry_total_detected": len(items),
        # Diagnostic
        "model": result.get("model", "unknown"),
    }
