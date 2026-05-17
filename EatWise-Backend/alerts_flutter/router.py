"""Flutter-compatible /api/alerts/ endpoints.

Routes:
  GET  /api/alerts/sfda/                 → SFDA recall/warning feed (public)
  GET  /api/alerts/personal/             → alerts generated for this user (auth)
  POST /api/alerts/{alert_id}/ack/       → mark a personal alert as read (auth)
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.core import models, security
from app.core.database import get_db
from app.core.errors import err_not_found, err_unauthorized


router = APIRouter(prefix="/alerts", tags=["Alerts (Flutter)"])


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
    return db.query(models.User).filter(models.User.id == uid, models.User.is_active == True).first()


# ============================================================
# SFDA public feed
# ============================================================
@router.get("/sfda/")
def sfda_alerts(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (db.query(models.SFDAAlert)
              .order_by(models.SFDAAlert.published_at.desc().nullslast())
              .limit(limit).all())
    return [{
        "id": a.id,
        "sfda_ref": a.sfda_ref or "",
        "title": a.title_ar or a.title_en or "",
        "title_en": a.title_en or "",
        "title_ar": a.title_ar or "",
        "alert_type": a.alert_type or "warning",
        "severity": a.severity or "medium",
        "product_name": a.product_name or "",
        "source_url": a.source_url or "",
        "published_at": a.published_at.isoformat() if a.published_at else "",
    } for a in rows]


# ============================================================
# Personal alerts for the authenticated user
# ============================================================
@router.get("/personal/")
def personal_alerts(
    unread_only: bool = False,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _try_user(authorization, db)
    if not user:
        raise err_unauthorized("Unauthorized")

    # Auto-generate personal alerts for each chronic condition / allergy.
    # Kept idempotent — we only create rows that don't already exist.
    _seed_personal_alerts_if_missing(db, user)

    query = db.query(models.UserAlert).filter(models.UserAlert.user_id == user.id)
    if unread_only:
        query = query.filter(models.UserAlert.acknowledged_at.is_(None))
    rows = query.order_by(models.UserAlert.created_at.desc()).limit(50).all()

    return [{
        "id": a.id,
        "kind": a.kind,
        "title": a.title,
        "body": a.body or "",
        "sfda_alert_id": a.sfda_alert_id,
        "acknowledged": a.acknowledged_at is not None,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else "",
        "created_at": a.created_at.isoformat(),
    } for a in rows]


def _seed_personal_alerts_if_missing(db: Session, user: models.User):
    """Create introductory personal alerts based on the user's profile.
    Runs once per unique alert-kind per user (idempotent)."""
    ap = db.query(models.AccountProfile).filter(
        models.AccountProfile.user_id == user.id
    ).first()
    if not ap:
        return

    def _has(kind: str, key: str) -> bool:
        return db.query(models.UserAlert).filter(
            models.UserAlert.user_id == user.id,
            models.UserAlert.kind == kind,
            models.UserAlert.title.like(f"%{key}%"),
        ).first() is not None

    # Allergies
    if ap.allergies and ap.allergies != "None":
        for a in [x.strip() for x in ap.allergies.split(",") if x.strip()]:
            if not _has("allergen", a):
                db.add(models.UserAlert(
                    user_id=user.id, kind="allergen",
                    title=f"Allergy alert: {a}",
                    body=f"We'll warn you whenever a scanned product or recipe may contain {a.lower()}.",
                ))
    # Chronic condition
    if ap.health_condition and ap.health_condition != "None":
        if not _has("condition", ap.health_condition):
            advice_map = {
                "Diabetes": "Prefer low-sugar, high-fiber foods. We'll flag high-sugar items.",
                "Blood Pressure": "Watch sodium intake. We'll flag very salty items.",
                "Heart Disease": "Prefer lean protein and healthy fats. We'll flag high-saturated-fat items.",
            }
            db.add(models.UserAlert(
                user_id=user.id, kind="condition",
                title=f"Health alert: {ap.health_condition}",
                body=advice_map.get(ap.health_condition, "We'll adjust recommendations to your condition."),
            ))
    # Mirror the most recent SFDA alerts into the personal feed (informational)
    recent_sfda = db.query(models.SFDAAlert).order_by(
        models.SFDAAlert.published_at.desc().nullslast()
    ).limit(3).all()
    for s in recent_sfda:
        title = f"SFDA: {s.title_ar or s.title_en or s.product_name or 'Alert'}"
        if not _has("sfda", title[:40]):
            db.add(models.UserAlert(
                user_id=user.id, kind="sfda",
                sfda_alert_id=s.id,
                title=title,
                body=s.title_en or "",
            ))
    db.commit()


@router.post("/{alert_id}/ack/", status_code=status.HTTP_204_NO_CONTENT)
def acknowledge(
    alert_id: int,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    user = _try_user(authorization, db)
    if not user:
        raise err_unauthorized("Unauthorized")
    a = db.query(models.UserAlert).filter(
        models.UserAlert.id == alert_id,
        models.UserAlert.user_id == user.id,
    ).first()
    if not a:
        raise err_not_found("Alert not found")
    a.acknowledged_at = datetime.utcnow()
    db.commit()
    return None
