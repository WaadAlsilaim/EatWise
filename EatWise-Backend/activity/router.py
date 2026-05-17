"""Activity logging and summaries."""
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core import models
from app.core.database import get_db
from app.core.errors import err_invalid_request
from app.core.responses import ok


router = APIRouter(prefix="/activity", tags=["Activity"])

# Rough kcal per unit (approximations)
KCAL_RATES = {
    ("steps", "steps"): 0.04,        # ~0.04 kcal per step
    ("run", "minutes"): 10.0,        # ~10 kcal/min running
    ("walk", "minutes"): 4.0,
    ("gym", "minutes"): 7.0,
    ("cycle", "minutes"): 8.0,
    ("swim", "minutes"): 9.0,
}


def estimate_kcal(activity_type: str, unit: str, amount: float) -> float:
    rate = KCAL_RATES.get((activity_type, unit), 0)
    return round(amount * rate, 2)


@router.post("", status_code=status.HTTP_201_CREATED)
def log_activity(
    body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        activity_type = body["activity_type"]
        amount = float(body["amount"])
        unit = body["unit"]
        occurred_at = body.get("occurred_at")
        if occurred_at:
            occurred_at = datetime.fromisoformat(occurred_at.replace("Z", "+00:00")).replace(tzinfo=None)
        else:
            occurred_at = datetime.utcnow()
    except (KeyError, ValueError) as e:
        raise err_invalid_request(f"Invalid payload: {e}")

    kcal = estimate_kcal(activity_type, unit, amount)
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

    return ok({
        "id": log.id,
        "activity_type": log.activity_type,
        "amount": float(log.amount),
        "unit": log.unit,
        "kcal_burned": float(log.kcal_burned),
        "occurred_at": log.occurred_at.isoformat(),
    })


@router.get("/summary")
def summary(
    range: Literal["day", "week", "month"] = Query("week"),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    if range == "day":
        start = now - timedelta(days=1)
    elif range == "month":
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(days=7)

    rows = (db.query(models.ActivityLog)
              .filter(models.ActivityLog.user_id == user.id,
                      models.ActivityLog.occurred_at >= start)
              .order_by(models.ActivityLog.occurred_at.desc())
              .all())

    total_kcal = sum(float(r.kcal_burned or 0) for r in rows)
    return ok({
        "range": range,
        "from": start.isoformat(),
        "to": now.isoformat(),
        "total_kcal_burned": round(total_kcal, 2),
        "entries": [{
            "id": r.id, "activity_type": r.activity_type,
            "amount": float(r.amount), "unit": r.unit,
            "kcal_burned": float(r.kcal_burned or 0),
            "occurred_at": r.occurred_at.isoformat(),
        } for r in rows]
    })
