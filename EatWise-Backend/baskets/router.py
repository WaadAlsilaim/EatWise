"""Baskets router: upload image, manage items."""
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.baskets import services
from app.core import models
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import err_invalid_request, err_not_found
from app.core.responses import ok


router = APIRouter(prefix="/baskets", tags=["Baskets"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_basket(
    background: BackgroundTasks,
    image: UploadFile = File(...),
    source: str = Form("upload"),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if source not in ("camera", "upload"):
        raise err_invalid_request("source must be 'camera' or 'upload'")
    if image.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise err_invalid_request("Only JPEG or PNG images accepted")

    # Read + size-check
    data = await image.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise err_invalid_request(f"Image exceeds {settings.max_upload_mb} MB limit")

    # Save under storage/baskets/<uuid>.<ext>
    ext = ".jpg" if image.content_type in ("image/jpeg", "image/jpg") else ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    storage_root = Path(settings.storage_dir) / "baskets"
    storage_root.mkdir(parents=True, exist_ok=True)
    fpath = storage_root / filename
    fpath.write_bytes(data)

    basket = models.Basket(
        user_id=user.id,
        image_path=str(fpath.relative_to(Path(settings.storage_dir).parent)),
        source=source,
        status="processing",
    )
    db.add(basket)
    db.commit()
    db.refresh(basket)

    background.add_task(services.process_basket, db, basket.id)

    return ok({"basket_id": basket.id, "status": basket.status})


def _serialize_basket(basket: models.Basket, db: Session, user: models.User) -> dict:
    items = []
    for it in basket.items:
        food_ref = None
        if it.food:
            food_ref = {
                "id": it.food.id,
                "name_ar": it.food.name_ar,
                "name_en": it.food.name_en,
                "category": it.food.category,
            }
        items.append({
            "id": it.id,
            "food": food_ref,
            "raw_label": it.raw_label,
            "confidence": float(it.confidence) if it.confidence else None,
            "quantity": float(it.quantity),
            "unit": it.unit,
            "manual": it.manual,
        })

    summary = services.compute_summary(basket)
    alerts = services.detect_alerts(db, user, basket)

    return {
        "id": basket.id,
        "status": basket.status,
        "source": basket.source,
        "image_path": basket.image_path,
        "items": items,
        "summary": summary,
        "alerts": alerts,
        "created_at": basket.created_at.isoformat(),
        "processed_at": basket.processed_at.isoformat() if basket.processed_at else None,
    }


@router.get("")
def list_baskets(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
):
    rows = (db.query(models.Basket)
              .filter(models.Basket.user_id == user.id)
              .order_by(models.Basket.created_at.desc())
              .limit(limit).all())
    return ok([{
        "id": b.id, "status": b.status, "source": b.source,
        "created_at": b.created_at.isoformat(),
        "items_count": len(b.items),
    } for b in rows])


@router.get("/{basket_id}")
def get_basket(
    basket_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    basket = db.query(models.Basket).filter(
        models.Basket.id == basket_id,
        models.Basket.user_id == user.id,
    ).first()
    if not basket:
        raise err_not_found("Basket not found")
    return ok(_serialize_basket(basket, db, user))


@router.post("/{basket_id}/items", status_code=status.HTTP_201_CREATED)
def add_item(
    basket_id: int,
    body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    basket = db.query(models.Basket).filter(
        models.Basket.id == basket_id,
        models.Basket.user_id == user.id,
    ).first()
    if not basket:
        raise err_not_found("Basket not found")

    food_id = body.get("food_id")
    quantity = float(body.get("quantity", 1))
    unit = body.get("unit", "piece")
    if not food_id:
        raise err_invalid_request("food_id is required")

    food = db.query(models.FoodItem).filter(models.FoodItem.id == food_id).first()
    if not food:
        raise err_not_found("Food not found")

    item = models.BasketItem(
        basket_id=basket.id, food_id=food_id,
        quantity=quantity, unit=unit, manual=True,
    )
    db.add(item)
    db.commit()
    db.refresh(basket)
    return ok(_serialize_basket(basket, db, user))


@router.patch("/{basket_id}/items/{item_id}")
def update_item(
    basket_id: int, item_id: int, body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (db.query(models.BasketItem)
              .join(models.Basket)
              .filter(models.BasketItem.id == item_id,
                      models.Basket.id == basket_id,
                      models.Basket.user_id == user.id)
              .first())
    if not item:
        raise err_not_found("Item not found")

    if "food_id" in body and body["food_id"]:
        item.food_id = int(body["food_id"])
    if "quantity" in body:
        item.quantity = float(body["quantity"])
    if "unit" in body:
        item.unit = str(body["unit"])
    db.commit()
    basket = db.query(models.Basket).filter(models.Basket.id == basket_id).first()
    return ok(_serialize_basket(basket, db, user))


@router.delete("/{basket_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    basket_id: int, item_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (db.query(models.BasketItem)
              .join(models.Basket)
              .filter(models.BasketItem.id == item_id,
                      models.Basket.id == basket_id,
                      models.Basket.user_id == user.id)
              .first())
    if item:
        db.delete(item)
        db.commit()
    return None


@router.delete("/{basket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_basket(
    basket_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    basket = db.query(models.Basket).filter(
        models.Basket.id == basket_id,
        models.Basket.user_id == user.id,
    ).first()
    if basket:
        # Remove image file if exists
        try:
            full_path = Path(settings.storage_dir).parent / basket.image_path
            if full_path.exists():
                os.remove(full_path)
        except Exception:
            pass
        db.delete(basket)
        db.commit()
    return None
