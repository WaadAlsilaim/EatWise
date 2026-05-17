"""Auth Pydantic schemas (request/response bodies)."""
import re
from pydantic import BaseModel, Field, field_validator


SAUDI_PHONE_RE = re.compile(r"^\+9665\d{8}$")


class RequestOTPIn(BaseModel):
    phone: str = Field(..., description="E.164 Saudi mobile, e.g. +966501234567")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if v.startswith("05") and len(v) == 10:
            v = "+966" + v[1:]
        elif v.startswith("5") and len(v) == 9:
            v = "+966" + v
        if not SAUDI_PHONE_RE.match(v):
            raise ValueError("Phone must be a valid Saudi mobile number")
        return v


class RequestOTPOut(BaseModel):
    expires_in: int
    resend_after: int
    dev_code: str | None = None  # populated only in dev mode (no SMS provider)


class VerifyOTPIn(BaseModel):
    phone: str
    code: str = Field(..., min_length=4, max_length=8)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return RequestOTPIn.validate_phone(v)


class UserOut(BaseModel):
    id: int
    display_name: str | None = None
    locale: str = "ar"
    phone_masked: str


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    access_ttl: int
    refresh_ttl: int
    user: UserOut


class RefreshIn(BaseModel):
    refresh_token: str
