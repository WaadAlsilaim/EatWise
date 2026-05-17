"""Flutter-compatible accounts endpoints.

Matches exactly what lib/features/auth/ + lib/features/profile/ + lib/features/more/
in the Flutter app expect. Keep this API stable; Flutter screens depend on the
exact field names here.

Routes (all under /api/accounts/):
    POST   /send-otp/      { phone_number } → { success, message, dev_code? }
    POST   /verify-otp/    { phone_number, code|otp } → { access, refresh, user }
    GET    /me/            → full profile (Flutter-shaped)
    PATCH  /me/update/     → update profile
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from fastapi import Query

from app.auth import services as auth_services
from app.auth.dependencies import get_current_user
from app.auth.schemas import RequestOTPIn, VerifyOTPIn
from app.core import models, security
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import err_invalid_request, err_unauthorized


router = APIRouter(prefix="/accounts", tags=["Accounts (Flutter)"])


# ============================================================
# OTP endpoints
# ============================================================
class _PhoneIn:
    pass


@router.post("/send-otp/")
def send_otp(body: dict, db: Session = Depends(get_db)):
    """
    Request body: { "phone_number": "+966501234567" }  OR { "phone": "..." }
    Response 200: { "success": true, "message": "...", "dev_code": "123456" }
                  (dev_code only when no SMS provider is configured)
    """
    phone = body.get("phone_number") or body.get("phone")
    if not phone:
        return {"success": False, "error": "phone_number is required"}

    # Reuse validation from existing schema
    try:
        parsed = RequestOTPIn(phone=phone).phone
    except ValueError as e:
        return {"success": False, "error": str(e)}

    ttl, resend, dev_code = auth_services.issue_otp(db, parsed)

    resp = {
        "success": True,
        "message": "OTP sent successfully",
        "expires_in": ttl,
        "resend_after": resend,
    }
    if dev_code:
        resp["dev_code"] = dev_code  # only in dev mode
    return resp


@router.post("/verify-otp/")
def verify_otp(body: dict, db: Session = Depends(get_db)):
    """
    Request body: { "phone_number": "...", "code"|"otp": "123456" }
    Response 200: { "access": "<jwt>", "refresh": "<token>", "user": {...} }
    Response 400/401: { "error": "..." }
    """
    phone = body.get("phone_number") or body.get("phone")
    code = body.get("code") or body.get("otp")
    if not phone or not code:
        return {"error": "phone_number and code are required"}, 400

    try:
        parsed = VerifyOTPIn(phone=phone, code=str(code)).phone
    except ValueError as e:
        return {"error": str(e)}, 400

    try:
        user, _created = auth_services.verify_otp(db, parsed, str(code))
    except Exception as exc:
        # Map our internal AppError details to Flutter-friendly { error }
        from fastapi import HTTPException
        if isinstance(exc, HTTPException):
            detail = exc.detail if isinstance(exc.detail, dict) else {"title": str(exc.detail)}
            return {"error": detail.get("detail") or detail.get("title", "OTP verification failed")}, exc.status_code
        raise

    pair = auth_services.issue_token_pair(db, user)

    # Ensure an AccountProfile row exists
    ap = db.query(models.AccountProfile).filter(models.AccountProfile.user_id == user.id).first()
    if not ap:
        ap = models.AccountProfile(user_id=user.id, allergies="None", health_condition="None", health_goal="Maintain")
        db.add(ap)
        db.commit()

    phone_plain = security.decrypt_phone(user.phone_enc)
    masked = phone_plain[:5] + "****" + phone_plain[-4:]

    return {
        "access": pair["access_token"],
        "refresh": pair["refresh_token"],
        "user": {
            "id": user.id,
            "phone_number": masked,
            "full_name": ap.full_name,
        },
    }


# ============================================================
# Profile endpoints (exact Flutter contract)
# ============================================================
def _serialize_profile(ap: models.AccountProfile | None, user: models.User) -> dict:
    return {
        "id": user.id,
        "full_name": ap.full_name if ap else None,
        "age": ap.age if ap else None,
        "height": float(ap.height) if ap and ap.height is not None else None,
        "weight": float(ap.weight) if ap and ap.weight is not None else None,
        "health_goal": (ap.health_goal if ap and ap.health_goal else "Weight Loss"),
        "health_condition": (ap.health_condition if ap and ap.health_condition else "None"),
        "allergies": (ap.allergies if ap and ap.allergies else "None"),
    }


@router.get("/me/")
def get_me(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ap = db.query(models.AccountProfile).filter(models.AccountProfile.user_id == user.id).first()
    if not ap:
        ap = models.AccountProfile(user_id=user.id)
        db.add(ap)
        db.commit()
        db.refresh(ap)
    return _serialize_profile(ap, user)


# ============================================================
# Daily summary used by the Dashboard
# ============================================================
@router.get("/daily-summary/")
def daily_summary(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sum today's saved meals + activity for the home screen progress ring."""
    from datetime import datetime
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())

    saved_today = db.query(models.SavedMeal).filter(
        models.SavedMeal.user_id == user.id,
        models.SavedMeal.created_at >= today_start,
    ).all()
    total_kcal = sum(int(m.calories or 0) for m in saved_today)
    total_protein = sum(float(m.protein or 0) for m in saved_today)
    total_carbs = sum(float(m.carbs or 0) for m in saved_today)
    total_fat = sum(float(m.fat or 0) for m in saved_today)

    activity_today = db.query(models.ActivityLog).filter(
        models.ActivityLog.user_id == user.id,
        models.ActivityLog.occurred_at >= today_start,
    ).all()
    burned_kcal = sum(float(a.kcal_burned or 0) for a in activity_today)

    ap = db.query(models.AccountProfile).filter(
        models.AccountProfile.user_id == user.id
    ).first()

    # ----- Personalized daily kcal target -----------------------------------
    # Uses Mifflin-St Jeor BMR formula × activity factor (TDEE), then adjusts
    # for the user's stated health goal:
    #   • Weight Loss → −500 kcal/day (≈0.5 kg loss per week, safe rate)
    #   • Maintain    → TDEE as-is
    #   • Muscle Gain → +400 kcal/day (lean bulk)
    target_kcal, target_protein, target_carbs, target_fat, plan = \
        _personalized_daily_targets(ap)

    return {
        "target_kcal": target_kcal,
        "consumed_kcal": int(total_kcal),
        "burned_kcal": round(burned_kcal, 1),
        "net_kcal": max(int(total_kcal) - int(burned_kcal), 0),
        "remaining_kcal": max(target_kcal - (int(total_kcal) - int(burned_kcal)), 0),
        "protein": {"consumed": round(total_protein, 1), "target": target_protein},
        "carbs":   {"consumed": round(total_carbs, 1),   "target": target_carbs},
        "fat":     {"consumed": round(total_fat, 1),     "target": target_fat},
        "meals_today": len(saved_today),
        "activities_today": len(activity_today),
        "plan": plan,   # diagnostic info — Flutter ignores it but useful for debugging
    }


def _personalized_daily_targets(
    ap: "models.AccountProfile | None",
) -> tuple[int, int, int, int, dict]:
    """Compute personalized kcal + macro targets from the user's profile.

    Algorithm (the standard sports-nutrition approach):
      1. BMR  — Mifflin-St Jeor equation (the most accurate non-clinical formula).
                We don't store sex, so we use the average constant (−78), which
                falls between the male (+5) and female (−161) variants. This
                gives a sensible estimate across users.
      2. TDEE — BMR × 1.4 (light activity, the most common assumption).
      3. Goal — adjust TDEE by ±500/+400 kcal depending on the user's goal.
      4. Macros — split kcal into protein/carbs/fat using goal-specific ratios.

    Returns (kcal, protein_g, carbs_g, fat_g, plan_dict)
    """
    # ---- Sane defaults if profile is missing -------------------------------
    age    = float(ap.age)    if ap and ap.age    else 25.0
    height = float(ap.height) if ap and ap.height else 170.0
    weight = float(ap.weight) if ap and ap.weight else 70.0
    goal   = (ap.health_goal if ap and ap.health_goal else "Maintain").strip().lower()

    # ---- Step 1: BMR via Mifflin-St Jeor (sex-averaged) --------------------
    bmr = 10.0 * weight + 6.25 * height - 5.0 * age - 78.0
    if bmr < 1000:    # safety floor
        bmr = 1000.0

    # ---- Step 2: TDEE ------------------------------------------------------
    activity_factor = 1.4   # lightly active (default)
    tdee = bmr * activity_factor

    # ---- Step 3: Goal adjustment ------------------------------------------
    if "loss" in goal or "lose" in goal:
        target_kcal = tdee - 500
        protein_pct, carbs_pct, fat_pct = 0.35, 0.35, 0.30  # higher protein for satiety
        plan_label = "Weight loss (deficit −500 kcal)"
    elif "muscle" in goal or "gain" in goal or "bulk" in goal:
        target_kcal = tdee + 400
        protein_pct, carbs_pct, fat_pct = 0.30, 0.50, 0.20  # high carbs for energy
        plan_label = "Muscle gain (surplus +400 kcal)"
    else:
        target_kcal = tdee
        protein_pct, carbs_pct, fat_pct = 0.25, 0.50, 0.25  # balanced
        plan_label = "Maintain (TDEE as-is)"

    # Reasonable bounds (1200–4000 kcal)
    target_kcal = max(1200, min(4000, int(round(target_kcal))))

    # ---- Step 4: Macro split (1g protein = 4 kcal, carb = 4, fat = 9) -----
    target_protein = round(target_kcal * protein_pct / 4)
    target_carbs   = round(target_kcal * carbs_pct   / 4)
    target_fat     = round(target_kcal * fat_pct     / 9)

    plan = {
        "bmr":  int(round(bmr)),
        "tdee": int(round(tdee)),
        "goal": goal,
        "label": plan_label,
        "macro_split_pct": {
            "protein": int(protein_pct * 100),
            "carbs":   int(carbs_pct   * 100),
            "fat":     int(fat_pct     * 100),
        },
    }
    return target_kcal, target_protein, target_carbs, target_fat, plan


# ============================================================
# Real logout + account deletion
# ============================================================
@router.post("/logout/", status_code=204)
def logout(
    body: dict | None = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke the refresh token (if provided). Safe to call without a body."""
    refresh_raw = (body or {}).get("refresh_token") if body else None
    if refresh_raw:
        try:
            auth_services.revoke_refresh(db, refresh_raw)
        except Exception:
            pass
    return None


@router.delete("/me/", status_code=204)
def delete_account(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GDPR-style full deletion: remove the user and all related rows."""
    db.delete(user)
    db.commit()
    return None


# ============================================================
# Dev-only helper: fetch the most recent OTP code for a phone number.
# Disabled automatically whenever a real SMS provider is configured.
# ============================================================
@router.get("/dev/last-code/")
def dev_last_code(phone_number: str = Query(..., alias="phone_number")):
    """Returns the last dev-mode OTP for the given phone number.

    Example (paste in your browser):
      http://127.0.0.1:8000/api/accounts/dev/last-code/?phone_number=%2B966501234567

    URL-encoded + is %2B. You can also use 0501234567 format.
    """
    if settings.is_sms_enabled:
        return {"enabled": False,
                "message": "Dev endpoint is disabled when a real SMS gateway is configured."}

    try:
        phone_parsed = RequestOTPIn(phone=phone_number).phone
    except ValueError as e:
        return {"error": str(e)}

    phone_hash = security.hash_phone(phone_parsed)
    code = auth_services.get_dev_last_otp(phone_hash)
    if not code:
        return {"enabled": True, "phone": phone_parsed, "code": None,
                "hint": "No OTP issued yet for this number. Call /send-otp/ first."}
    return {"enabled": True, "phone": phone_parsed, "code": code}


@router.patch("/me/update/")
def update_me(
    body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ap = db.query(models.AccountProfile).filter(models.AccountProfile.user_id == user.id).first()
    if not ap:
        ap = models.AccountProfile(user_id=user.id)
        db.add(ap)
        db.flush()

    # Accept the exact field names Flutter sends
    if "full_name" in body:
        ap.full_name = str(body["full_name"])[:120] if body["full_name"] else None
    if "age" in body and body["age"] is not None:
        try:
            ap.age = int(body["age"])
        except (TypeError, ValueError):
            pass
    if "height" in body and body["height"] is not None:
        try:
            ap.height = float(body["height"])
        except (TypeError, ValueError):
            pass
    if "weight" in body and body["weight"] is not None:
        try:
            ap.weight = float(body["weight"])
        except (TypeError, ValueError):
            pass
    if "health_goal" in body and body["health_goal"]:
        ap.health_goal = str(body["health_goal"])[:40]
    if "health_condition" in body and body["health_condition"] is not None:
        ap.health_condition = str(body["health_condition"])[:40]
    if "allergies" in body:
        val = body["allergies"]
        ap.allergies = val if isinstance(val, str) else "None"

    db.commit()
    db.refresh(ap)
    return _serialize_profile(ap, user)
