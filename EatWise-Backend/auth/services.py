"""Auth business logic — OTP issuance, verification, token lifecycle."""
import sys
from datetime import datetime, timedelta
from typing import Tuple

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.core import models, security
from app.core.config import settings
from app.core.errors import (
    err_invalid_request, err_otp_expired, err_otp_locked, err_rate_limited,
    err_unauthorized
)


# Dev-only: remembers the most recent plaintext OTP per phone hash so we can
# surface it via /api/accounts/dev/last-code/ without keeping plaintext on disk.
# Never used when a real SMS provider is configured.
_DEV_LAST_OTP: dict[str, str] = {}


def get_dev_last_otp(phone_hash: str) -> str | None:
    return _DEV_LAST_OTP.get(phone_hash)


def _mask_phone(phone: str) -> str:
    # +9665XXXXXXXX  -> +9665****XXXX
    if len(phone) >= 10:
        return phone[:5] + "****" + phone[-4:]
    return phone


# ---------- OTP ----------
def issue_otp(db: Session, phone: str) -> Tuple[int, int, str | None]:
    """Create an OTP, rate-limit by phone, return (ttl_seconds, resend_after, dev_code_or_none)."""
    phone_h = security.hash_phone(phone)
    now = datetime.utcnow()

    # Rate limit: count non-used OTPs for this phone in the last minute
    recent = db.query(models.OTPCode).filter(
        models.OTPCode.phone_hash == phone_h,
        models.OTPCode.created_at >= now - timedelta(minutes=1),
    ).count()
    if recent >= settings.otp_rate_limit_per_minute:
        raise err_rate_limited()

    # Generate + store
    code = security.generate_otp()
    otp = models.OTPCode(
        phone_hash=phone_h,
        code_hash=security.hash_secret(code),
        expires_at=now + timedelta(minutes=settings.otp_expire_minutes),
    )
    db.add(otp)
    db.commit()

    # In dev mode (no SMS provider), return the code so the iOS developer can test.
    dev_code = code if not settings.is_sms_enabled else None

    # Also print to console (flushed) and remember in-memory for /dev/last-code/
    if not settings.is_sms_enabled:
        _DEV_LAST_OTP[phone_h] = code
        banner = (
            "\n" + "=" * 56 +
            f"\n  [DEV-MODE] OTP for {_mask_phone(phone)} = {code}\n" +
            "=" * 56 + "\n"
        )
        print(banner, flush=True)
        sys.stdout.flush()

    return settings.otp_expire_minutes * 60, 60, dev_code


def verify_otp(db: Session, phone: str, submitted_code: str) -> Tuple[models.User, bool]:
    """Returns (user, created_new). Raises on failure."""
    phone_h = security.hash_phone(phone)
    now = datetime.utcnow()

    otp = (
        db.query(models.OTPCode)
        .filter(
            models.OTPCode.phone_hash == phone_h,
            models.OTPCode.used_at.is_(None),
        )
        .order_by(desc(models.OTPCode.created_at))
        .first()
    )
    if not otp:
        raise err_unauthorized("No OTP requested for this number")

    if otp.attempts >= settings.otp_max_attempts:
        raise err_otp_locked()

    if otp.expires_at < now:
        raise err_otp_expired()

    if not security.verify_secret(submitted_code, otp.code_hash):
        otp.attempts += 1
        db.commit()
        if otp.attempts >= settings.otp_max_attempts:
            raise err_otp_locked()
        raise err_unauthorized("Invalid OTP code")

    # Success: mark used
    otp.used_at = now
    db.commit()

    # Create or fetch user
    user = db.query(models.User).filter(models.User.phone_hash == phone_h).first()
    created = False
    if not user:
        user = models.User(
            phone_hash=phone_h,
            phone_enc=security.encrypt_phone(phone),
            is_verified=True,
            locale="ar",
        )
        db.add(user)
        db.flush()

        # Also create empty health profile shell
        profile = models.HealthProfile(user_id=user.id)
        db.add(profile)
        created = True
    else:
        user.is_verified = True

    user.last_login_at = now
    db.commit()
    db.refresh(user)
    return user, created


# ---------- Tokens ----------
def issue_token_pair(db: Session, user: models.User, device_label: str | None = None) -> dict:
    access = security.create_access_token(subject=user.id)
    refresh_raw = security.create_refresh_token(subject=user.id)

    rec = models.RefreshToken(
        user_id=user.id,
        token_hash=security.hash_token(refresh_raw),
        device_label=device_label,
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(rec)
    db.commit()

    return {
        "access_token": access,
        "refresh_token": refresh_raw,
        "access_ttl": settings.access_token_expire_minutes * 60,
        "refresh_ttl": settings.refresh_token_expire_days * 86400,
    }


def rotate_refresh(db: Session, refresh_raw: str) -> dict:
    token_hash = security.hash_token(refresh_raw)
    rec = db.query(models.RefreshToken).filter(
        models.RefreshToken.token_hash == token_hash,
        models.RefreshToken.revoked_at.is_(None),
    ).first()
    if not rec or rec.expires_at < datetime.utcnow():
        raise err_unauthorized("Invalid or expired refresh token")

    # Revoke the old one
    rec.revoked_at = datetime.utcnow()
    db.flush()

    user = db.query(models.User).filter(models.User.id == rec.user_id).first()
    if not user or not user.is_active:
        raise err_unauthorized("User disabled")

    pair = issue_token_pair(db, user, device_label=rec.device_label)
    return pair


def revoke_refresh(db: Session, refresh_raw: str) -> None:
    token_hash = security.hash_token(refresh_raw)
    rec = db.query(models.RefreshToken).filter(
        models.RefreshToken.token_hash == token_hash,
        models.RefreshToken.revoked_at.is_(None),
    ).first()
    if rec:
        rec.revoked_at = datetime.utcnow()
        db.commit()
