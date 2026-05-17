"""Standardized error envelope (RFC 7807 style)."""
from fastapi import HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, title: str, detail: str = ""):
        super().__init__(status_code=status_code, detail={
            "type": code, "title": title, "status": status_code, "detail": detail
        })


async def app_error_handler(request: Request, exc: AppError):
    body = exc.detail if isinstance(exc.detail, dict) else {
        "type": "error", "title": str(exc.detail), "status": exc.status_code, "detail": ""
    }
    body["instance"] = str(request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": body}
    )


async def generic_http_handler(request: Request, exc: HTTPException):
    if isinstance(exc, AppError):
        return await app_error_handler(request, exc)
    body = {
        "type": "http_error",
        "title": exc.detail if isinstance(exc.detail, str) else "HTTP error",
        "status": exc.status_code,
        "detail": "",
        "instance": str(request.url.path),
    }
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": body})


# Common error constructors
def err_invalid_request(msg: str = "Invalid request"):
    return AppError(status.HTTP_400_BAD_REQUEST, "invalid_request", msg)

def err_unauthorized(msg: str = "Unauthorized"):
    return AppError(status.HTTP_401_UNAUTHORIZED, "unauthorized", msg)

def err_not_found(msg: str = "Not found"):
    return AppError(status.HTTP_404_NOT_FOUND, "not_found", msg)

def err_otp_expired():
    return AppError(status.HTTP_410_GONE, "otp_expired", "OTP has expired", "Please request a new one.")

def err_otp_locked(minutes: int = 15):
    return AppError(status.HTTP_423_LOCKED, "otp_locked", "Too many invalid attempts",
                    f"Try again after {minutes} minutes.")

def err_rate_limited():
    return AppError(status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited", "Too many requests")
