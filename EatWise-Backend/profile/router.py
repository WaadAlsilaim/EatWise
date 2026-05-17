"""Profile router."""
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core import models, security
from app.core.database import get_db
from app.core.errors import err_invalid_request, err_not_found
from app.core.responses import ok
from app.profile import schemas, services


router = APIRouter(prefix="/profile", tags=["Profile"])


def _build_profile_out(user: models.User, db: Session) -> dict:
    hp = user.health_profile
    phone_plain = security.decrypt_phone(user.phone_enc)
    masked = phone_plain[:5] + "****" + phone_plain[-4:]

    allergens = []
    for ua in user.allergens:
        a = ua.allergen
        allergens.append({
            "id": a.id, "slug": a.slug,
            "name_ar": a.name_ar, "name_en": a.name_en,
            "severity": ua.severity,
        })

    conditions = []
    for uc in user.conditions:
        c = uc.condition
        conditions.append({
            "id": c.id, "slug": c.slug,
            "name_ar": c.name_ar, "name_en": c.name_en,
        })

    health = {
        "gender": hp.gender if hp else None,
        "date_of_birth": hp.date_of_birth.date().isoformat() if hp and hp.date_of_birth else None,
        "height_cm": float(hp.height_cm) if hp and hp.height_cm else None,
        "weight_kg": float(hp.weight_kg) if hp and hp.weight_kg else None,
        "activity_level": hp.activity_level if hp else None,
        "goal": hp.goal if hp else None,
        "daily_kcal": hp.daily_kcal if hp else None,
    }

    return {
        "id": user.id,
        "display_name": user.display_name,
        "locale": user.locale,
        "phone_masked": masked,
        "health": health,
        "allergens": allergens,
        "conditions": conditions,
    }


@router.get("")
def get_profile(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(_build_profile_out(user, db))


@router.patch("")
def update_profile(
    body: schemas.ProfileUpdateIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.locale is not None:
        user.locale = body.locale

    if body.health:
        hp = user.health_profile
        if not hp:
            hp = models.HealthProfile(user_id=user.id)
            db.add(hp)
            db.flush()

        h = body.health
        if h.gender is not None:
            hp.gender = h.gender
        if h.date_of_birth is not None:
            hp.date_of_birth = datetime.combine(h.date_of_birth, datetime.min.time())
        if h.height_cm is not None:
            hp.height_cm = h.height_cm
        if h.weight_kg is not None:
            hp.weight_kg = h.weight_kg
        if h.activity_level is not None:
            hp.activity_level = h.activity_level
        if h.goal is not None:
            hp.goal = h.goal

        hp.daily_kcal = services.compute_daily_kcal(hp)

    db.commit()
    db.refresh(user)
    return ok(_build_profile_out(user, db))


@router.get("/allergens/catalog")
def list_allergens(db: Session = Depends(get_db)):
    rows = db.query(models.Allergen).order_by(models.Allergen.name_en).all()
    return ok([{"id": a.id, "slug": a.slug, "name_ar": a.name_ar, "name_en": a.name_en} for a in rows])


@router.post("/allergens", status_code=status.HTTP_201_CREATED)
def add_allergen(
    body: schemas.AllergenAddIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allergen = db.query(models.Allergen).filter(models.Allergen.id == body.allergen_id).first()
    if not allergen:
        raise err_not_found("Allergen not found")

    existing = db.query(models.UserAllergen).filter(
        models.UserAllergen.user_id == user.id,
        models.UserAllergen.allergen_id == body.allergen_id,
    ).first()
    if existing:
        existing.severity = body.severity
    else:
        db.add(models.UserAllergen(
            user_id=user.id, allergen_id=body.allergen_id, severity=body.severity
        ))
    db.commit()
    return ok({"status": "added"})


@router.delete("/allergens/{allergen_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_allergen(
    allergen_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.UserAllergen).filter(
        models.UserAllergen.user_id == user.id,
        models.UserAllergen.allergen_id == allergen_id,
    ).delete()
    db.commit()
    return None


@router.get("/conditions/catalog")
def list_conditions(db: Session = Depends(get_db)):
    rows = db.query(models.ChronicCondition).order_by(models.ChronicCondition.name_en).all()
    return ok([{"id": c.id, "slug": c.slug, "name_ar": c.name_ar, "name_en": c.name_en} for c in rows])


@router.post("/conditions", status_code=status.HTTP_201_CREATED)
def add_condition(
    body: schemas.ConditionAddIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cond = db.query(models.ChronicCondition).filter(models.ChronicCondition.id == body.condition_id).first()
    if not cond:
        raise err_not_found("Condition not found")

    exists = db.query(models.UserCondition).filter(
        models.UserCondition.user_id == user.id,
        models.UserCondition.condition_id == body.condition_id,
    ).first()
    if not exists:
        db.add(models.UserCondition(user_id=user.id, condition_id=body.condition_id))
        db.commit()
    return ok({"status": "added"})


@router.delete("/conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_condition(
    condition_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.UserCondition).filter(
        models.UserCondition.user_id == user.id,
        models.UserCondition.condition_id == condition_id,
    ).delete()
    db.commit()
    return None
