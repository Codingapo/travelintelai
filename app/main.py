from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import create_db_and_tables
from app.routers import bookings, analytics, events, agencies
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.api_bookings import router as api_bookings_router

app = FastAPI(
    title="TravelIntel AI",
    description=(
        "Central intelligence platform for travel agencies. "
        "Provides an admin dashboard, AI analytics, and a public REST API "
        "that external agency clients can use to create and manage bookings "
        "using their API key."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── Session middleware (used by the web dashboard only) ───────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "travelintel-super-secret-2026")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="ti_session",
    max_age=86400,
    https_only=os.environ.get("HTTPS_ONLY", "false").lower() == "true",
)

# ── Static files ──────────────────────────────────────────────────────────────
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

# ── DB startup ────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# ── Web dashboard routes ──────────────────────────────────────────────────────
app.include_router(auth_router)                # /, /register, /login, /logout
app.include_router(dashboard_router)           # /dashboard
app.include_router(bookings.router,  prefix="/bookings",  tags=["Dashboard — Bookings"])
app.include_router(analytics.router, prefix="/analytics", tags=["Dashboard — Analytics"])
app.include_router(events.router,    prefix="/events",    tags=["Dashboard — Events"])
app.include_router(agencies.router,  prefix="/agencies",  tags=["Dashboard — Agencies"])

# ── Public REST API (consumed by external clients like APO Agency) ────────────
app.include_router(api_bookings_router)        # /api/v1/...


@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "app": "TravelIntel AI",
        "version": "2.0.0",
        "api_base": "/api/v1",
        "docs": "/api/docs",
    }
