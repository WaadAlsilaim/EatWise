"""Security helpers: hashing, JWT, phone encryption."""
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- Phone hashing & encryption (lightweight) ----------
def hash_phone(phone: str) -> str:
    """Deterministic SHA-256 hash used for lookup (collision-resistant)."""
    return hashlib.sha256((settings.jwt_secret + phone).encode("utf-8")).hexdigest()


def encrypt_phone(phone: str) -> str:
    """
    Simple reversible encoding using XOR with the JWT secret.
    For production, replace with AES-256-GCM or use pgcrypto on the DB side.
    """
    key = settings.jwt_secret.encode("utf-8")
    data = phone.encode("utf-8")
    out = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(out).decode("ascii")


def decrypt_phone(token: str) -> str:
    key = settings.jwt_secret.encode("utf-8")
    data = base64.b64decode(token.encode("ascii"))
    out = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return out.decode("utf-8")


# ---------- Password / OTP hashing ----------
def hash_secret(secret: str) -> str:
    """bcrypt hash — used for OTP codes and refresh tokens."""
    return pwd_context.hash(secret)


def verify_secret(secret: str, hashed: str) -> bool:
    return pwd_context.verify(secret, hashed)


# ---------- OTP generation ----------
def generate_otp(length: int = None) -> str:
    length = length or settings.otp_length
    return "".join(secrets.choice("0123456789") for _ in range(length))


# ---------- JWT ----------
def create_access_token(subject: int, extra: dict = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: int) -> str:
    """Returns an opaque refresh token string. Its hash is stored in DB."""
    raw = secrets.token_urlsafe(48)
    return raw


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """HMAC-SHA256 of a token — faster than bcrypt for frequent refresh lookups."""
    return hmac.new(settings.jwt_secret.encode(), token.encode(), hashlib.sha256).hexdigest()
