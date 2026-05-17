"""FastAPI dependencies: extract current user from Authorization header."""
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core import models, security
from app.core.database import get_db
from app.core.errors import err_unauthorized


def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> models.User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise err_unauthorized("Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    payload = security.decode_access_token(token)
    if not payload:
        raise err_unauthorized("Invalid access token")

    user_id = int(payload.get("sub", 0))
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_active == True,
    ).first()
    if not user:
        raise err_unauthorized("User not found")
    return user
