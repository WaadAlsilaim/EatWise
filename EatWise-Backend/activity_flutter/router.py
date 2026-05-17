"""Flutter-compatible /api/activity/ endpoints.

Routes (all auth):
  POST /api/activity/log/          body {activity_type, amount, unit, occurred_at?}
  GET  /api/activity/logs/         paginated list of user's activity
  GET  /api/activity/summary/?range=day|week|month
  DELETE /api/activity/{id}/
  GET  /api/activity/suggestions/  suggestions based on the user's goal
"""
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core import models, security
from app.core.database import get_db
from app.core.errors import err_invalid_request, err_not_found, err_unauthorized


router = APIRouter(prefix="/activity", tags=["Activity (Flutter)"])

# kcal per unit approximations (generic population averages)
KCAL_RATES = {
    ("walk", "minutes"):   4.0,
    ("walk", "steps"):     0.04,
    ("steps", "steps"):    0.04,
    ("run", "minutes"):    10.0,
    ("run", "km"):         60.0,
    ("gym", "minutes"):    7.5,
    ("cycle", "minutes"):  8.0,
    ("swim", "minutes"):   9.0,
    ("yoga", "minutes"):   3.0,
    ("hiit", "minutes"):   12.0,
}


# Catalog shown in the app
ACTIVITY_CATALOG = [
    {"type": "walk",  "unit": "minutes", "label_ar": "مشي",  "label_en": "Walking",   "emoji": "🚶", "color_hex": "#DFF5E9"},
    {"type": "steps", "unit": "steps",   "label_ar": "خطوات", "label_en": "Steps",    "emoji": "👣", "color_hex": "#E0F4D7"},
    {"type": "run",   "unit": "minutes", "label_ar": "جري",   "label_en": "Running",  "emoji": "🏃", "color_hex": "#FFE8D6"},
    {"type": "cycle", "unit": "minutes", "label_ar": "دراجة", "label_en": "Cycling",  "emoji": "🚴", "color_hex": "#D6EEFD"},
    {"type": "gym",   "unit": "minutes", "label_ar": "نادي",  "label_en": "Gym",      "emoji": "🏋", "color_hex": "#FFE3C2"},
    {"type": "swim",  "unit": "minutes", "label_ar": "سباحة", "label_en": "Swimming", "emoji": "🏊", "color_hex": "#D6EEFD"},
    {"type": "yoga",  "unit": "minutes", "label_ar": "يوغا",  "label_en": "Yoga",     "emoji": "🧘", "color_hex": "#F5EAD2"},
    {"type": "hiit",  "unit": "minutes", "label_ar": "هيت",   "label_en": "HIIT",     "emoji": "💪", "color_hex": "#FFE1EC"},
]


def _require_user(authorization: str | None, db: Session) -> models.User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise err_unauthorized("Unauthorized")
    token = authorization.split(" ", 1)[1].strip()
    payload = security.decode_access_token(token)
    if not payload:
        raise err_unauthorized("Invalid token")
    try:
        uid = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        raise err_unauthorized("Invalid token")
    u = db.query(models.User).filter(models.User.id == uid, models.User.is_active == True).first()
    if not u:
        raise err_unauthorized("User not found")
    return u


def _serialize_log(log: models.ActivityLog) -> dict:
    meta = {a["type"]: a for a in ACTIVITY_CATALOG}.get(log.activity_type, {})
    return {
        "id": log.id,
        "activity_type": log.activity_type,
        "label_en": meta.get("label_en", log.activity_type.title()),
        "label_ar": meta.get("label_ar", log.activity_type),
        "emoji": meta.get("emoji", "🏃"),
        "color_hex": meta.get("color_hex", "#F2F2F2"),
        "amount": float(log.amount),
        "unit": log.unit,
        "kcal_burned": float(log.kcal_burned or 0),
        "occurred_at": log.occurred_at.isoformat(),
        "created_at": log.created_at.isoformat(),
    }


@router.get("/catalog/")
def activity_catalog():
    """List of activity types the app offers (used by the Flutter picker)."""
    return ACTIVITY_CATALOG


@router.post("/log/", status_code=status.HTTP_201_CREATED)
def log_activity(
    body: dict,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _require_user(authorization, db)
    try:
        activity_type = body["activity_type"]
        amount = float(body["amount"])
        unit = body.get("unit") or "minutes"
        occurred_at = body.get("occurred_at")
        if occurred_at:
            occurred_at = datetime.fromisoformat(
                occurred_at.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        else:
            occurred_at = datetime.utcnow()
    except (KeyError, ValueError, TypeError) as e:
        raise err_invalid_request(f"Invalid payload: {e}")

    kcal = round(amount * KCAL_RATES.get((activity_type, unit), 0), 2)
    log = models.ActivityLog(
        user_id=user.id,
        activity_type=activity_type,
        amount=amount, unit=unit,
        kcal_burned=kcal,
        occurred_at=occurred_at,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _serialize_log(log)


@router.get("/logs/")
def list_logs(
    limit: int = Query(30, ge=1, le=100),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _require_user(authorization, db)
    rows = (db.query(models.ActivityLog)
              .filter(models.ActivityLog.user_id == user.id)
              .order_by(models.ActivityLog.occurred_at.desc())
              .limit(limit).all())
    return [_serialize_log(r) for r in rows]


@router.get("/summary/")
def summary(
    range: Literal["day", "week", "month"] = Query("week"),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _require_user(authorization, db)
    now = datetime.utcnow()
    start = {
        "day":   now - timedelta(days=1),
        "week":  now - timedelta(days=7),
        "month": now - timedelta(days=30),
    }[range]

    rows = (db.query(models.ActivityLog)
              .filter(models.ActivityLog.user_id == user.id,
                      models.ActivityLog.occurred_at >= start)
              .order_by(models.ActivityLog.occurred_at.desc())
              .all())

    total_kcal = sum(float(r.kcal_burned or 0) for r in rows)
    by_type: dict[str, float] = {}
    for r in rows:
        by_type[r.activity_type] = by_type.get(r.activity_type, 0) + float(r.kcal_burned or 0)

    return {
        "range": range,
        "from": start.isoformat(),
        "to": now.isoformat(),
        "total_kcal_burned": round(total_kcal, 2),
        "total_entries": len(rows),
        "by_type": {k: round(v, 1) for k, v in by_type.items()},
        "entries": [_serialize_log(r) for r in rows[:30]],
    }


@router.delete("/{log_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(
    log_id: int,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _require_user(authorization, db)
    log = db.query(models.ActivityLog).filter(
        models.ActivityLog.id == log_id,
        models.ActivityLog.user_id == user.id,
    ).first()
    if not log:
        raise err_not_found("Activity log not found")
    db.delete(log)
    db.commit()
    return None


@router.get("/suggestions/")
def suggestions(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    """Suggest activities to balance today's intake vs the user's goal."""
    user = _require_user(authorization, db)

    # Today's intake from saved meals
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    saved_today = db.query(models.SavedMeal).filter(
        models.SavedMeal.user_id == user.id,
        models.SavedMeal.created_at >= today_start,
    ).all()
    intake = sum(int(m.calories or 0) for m in saved_today)

    # Today's burn
    burned_today = sum(
        float(r.kcal_burned or 0)
        for r in db.query(models.ActivityLog).filter(
            models.ActivityLog.user_id == user.id,
            models.ActivityLog.occurred_at >= today_start,
        ).all()
    )

    # Daily goal (from AccountProfile — rough rule)
    ap = db.query(models.AccountProfile).filter(
        models.AccountProfile.user_id == user.id
    ).first()
    target_kcal = 2000  # sensible default
    if ap and ap.weight:
        target_kcal = int(float(ap.weight) * 30)  # simple approximation

    deficit = intake - int(burned_today)  # positive = needs to burn
    needs_burn = max(deficit - target_kcal, 0)

    tips: list[str] = []
    if needs_burn > 0:
        walk_min = int(round(needs_burn / KCAL_RATES[("walk", "minutes")]))
        run_min = int(round(needs_burn / KCAL_RATES[("run", "minutes")]))
        tips.append(f"Walk for {walk_min} minutes to balance today's extra {needs_burn} kcal")
        tips.append(f"Or run for {run_min} minutes")
    else:
        tips.append("You're on track for today. A gentle 20-minute walk still helps digestion.")

    return {
        "target_kcal": target_kcal,
        "intake_today": intake,
        "burned_today": round(burned_today, 1),
        "surplus_kcal": max(needs_burn, 0),
        "tips": tips,
    }
