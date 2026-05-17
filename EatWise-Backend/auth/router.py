"""Auth router — OTP request/verify, refresh, logout."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import schemas, services, dependencies as deps
from app.core import models, security
from app.core.database import get_db
from app.core.responses import ok


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/request-otp", status_code=status.HTTP_202_ACCEPTED)
def request_otp(body: schemas.RequestOTPIn, db: Session = Depends(get_db)):
    ttl, resend, dev_code = services.issue_otp(db, body.phone)
    return ok(schemas.RequestOTPOut(
        expires_in=ttl, resend_after=resend, dev_code=dev_code
    ).model_dump())


@router.post("/verify-otp")
def verify_otp(body: schemas.VerifyOTPIn, db: Session = Depends(get_db)):
    user, _created = services.verify_otp(db, body.phone, body.code)
    pair = services.issue_token_pair(db, user)
    phone_plain = security.decrypt_phone(user.phone_enc)
    masked = phone_plain[:5] + "****" + phone_plain[-4:]
    return ok({
        **pair,
        "user": schemas.UserOut(
            id=user.id,
            display_name=user.display_name,
            locale=user.locale,
            phone_masked=masked,
        ).model_dump(),
    })


@router.post("/refresh")
def refresh(body: schemas.RefreshIn, db: Session = Depends(get_db)):
    pair = services.rotate_refresh(db, body.refresh_token)
    return ok(pair)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: schemas.RefreshIn,
    db: Session = Depends(get_db),
    _user: models.User = Depends(deps.get_current_user),
):
    services.revoke_refresh(db, body.refresh_token)
    return None


@router.get("/me")
def me(user: models.User = Depends(deps.get_current_user)):
    phone_plain = security.decrypt_phone(user.phone_enc)
    masked = phone_plain[:5] + "****" + phone_plain[-4:]
    return ok(schemas.UserOut(
        id=user.id, display_name=user.display_name,
        locale=user.locale, phone_masked=masked,
    ).model_dump())
