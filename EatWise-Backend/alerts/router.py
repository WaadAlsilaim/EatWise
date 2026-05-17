"""Alerts router: SFDA feed + personalized alerts."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core import models
from app.core.database import get_db
from app.core.errors import err_not_found
from app.core.responses import ok


router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/sfda")
def list_sfda_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.SFDAAlert).order_by(models.SFDAAlert.published_at.desc().nullslast())
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    return ok({
        "page": page, "per_page": per_page, "total": total,
        "items": [{
            "id": a.id, "sfda_ref": a.sfda_ref,
            "title_ar": a.title_ar, "title_en": a.title_en,
            "alert_type": a.alert_type, "severity": a.severity,
            "product_name": a.product_name, "source_url": a.source_url,
            "published_at": a.published_at.isoformat() if a.published_at else None,
        } for a in rows]
    })


@router.get("/personal")
def list_personal_alerts(
    unread: bool = False,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.UserAlert).filter(models.UserAlert.user_id == user.id)
    if unread:
        query = query.filter(models.UserAlert.acknowledged_at.is_(None))
    rows = query.order_by(models.UserAlert.created_at.desc()).limit(50).all()
    return ok([{
        "id": a.id, "kind": a.kind, "title": a.title, "body": a.body,
        "sfda_alert_id": a.sfda_alert_id,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        "created_at": a.created_at.isoformat(),
    } for a in rows])


@router.post("/{alert_id}/acknowledge", status_code=204)
def acknowledge(
    alert_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.query(models.UserAlert).filter(
        models.UserAlert.id == alert_id,
        models.UserAlert.user_id == user.id,
    ).first()
    if not a:
        raise err_not_found("Alert not found")
    a.acknowledged_at = datetime.utcnow()
    db.commit()
    return None
