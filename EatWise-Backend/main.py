"""FastAPI entry point.

Run locally:
    uvicorn app.main:app --reload

The server exposes Swagger UI at /docs and ReDoc at /redoc.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.database import Base, engine
from app.core.errors import AppError, app_error_handler, generic_http_handler
from app.core import models  # noqa: F401 — registers ORM models with Base

from app.auth.router import router as auth_router
from app.profile.router import router as profile_router
from app.recipes.router import router as recipes_router
from app.baskets.router import router as baskets_router
from app.recommendations.router import router as recommendations_router
from app.alerts.router import router as alerts_router
from app.activity.router import router as activity_router

# Flutter-compatible routers (matches the existing iOS-frontend-main app)
from app.accounts.router import router as accounts_router
from app.products_api.router import router as products_flutter_router
from app.meals.router import router as meals_router
from app.analyze.router import router as analyze_router
from app.alerts_flutter.router import router as alerts_flutter_router
from app.activity_flutter.router import router as activity_flutter_router
from app.pantry.router import router as pantry_router


# Ensure tables exist at startup (SQLite convenience)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EatWise API",
    version="1.0.0",
    description=(
        "Backend for the EatWise iOS application.\n\n"
        "• OTP + JWT authentication\n"
        "• Health profile management\n"
        "• Grocery basket upload and nutrition summary\n"
        "• Recipe catalogue + hybrid recommendations\n"
        "• SFDA & personal alerts\n"
        "• Activity tracking\n"
    ),
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — permissive in development so the Flutter app (running on an emulator
# or a real device on the LAN) can connect without origin restrictions.
# In production, tighten this via .env (CORS_ORIGINS).
_cors_origins = ["*"] if settings.app_env == "development" else settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False if _cors_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Error handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, generic_http_handler)


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "server_error",
                "title": "Internal server error",
                "status": 500,
                "detail": str(exc) if settings.debug else "",
                "instance": str(request.url.path),
            },
        },
    )


# Health endpoint
@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/", tags=["Meta"])
def root():
    return {
        "name": "EatWise API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Static image serving (basket images, in dev only)
storage_path = Path(settings.storage_dir)
storage_path.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")


# Register routers under /api/v1 (internal, detailed API)
prefix = settings.api_v1_prefix
app.include_router(auth_router, prefix=prefix)
app.include_router(profile_router, prefix=prefix)
app.include_router(recipes_router, prefix=prefix)
app.include_router(baskets_router, prefix=prefix)
app.include_router(recommendations_router, prefix=prefix)
app.include_router(alerts_router, prefix=prefix)
app.include_router(activity_router, prefix=prefix)

# Flutter-compatible routes under /api/...  (matches lib/features/*)
app.include_router(accounts_router, prefix="/api")
app.include_router(products_flutter_router, prefix="/api")
app.include_router(meals_router, prefix="/api")
app.include_router(alerts_flutter_router, prefix="/api")
app.include_router(activity_flutter_router, prefix="/api")
app.include_router(pantry_router, prefix="/api")

# Analyze endpoint is at /analyze-image (no prefix) to match food_service.dart
app.include_router(analyze_router)
