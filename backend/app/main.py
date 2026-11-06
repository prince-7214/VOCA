"""
VOCA API — main FastAPI application entry point.

Serves both the API and the React frontend (when built) from a single process.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.database.connection import engine, Base

# Import models first so they register with Base.metadata
from app.models.expense import Expense  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.reminder import Reminder  # noqa: F401
from app.models.command_history import CommandHistory  # noqa: F401
from app.models.conversation_context import ConversationContext  # noqa: F401
from app.models.contact import Contact  # noqa: F401
from app.models.email_message import EmailMessage  # noqa: F401
from app.models.user import User  # noqa: F401

# Create tables immediately on module load to guarantee persistence and table existence
Base.metadata.create_all(bind=engine)

# Import routers
from app.api.routes.voice import router as voice_router
from app.api.routes.expenses import router as expenses_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.reminders import router as reminders_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.history import router as history_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.contacts import router as contacts_router
from app.api.routes.emails import router as emails_router
from app.api.routes.auth import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine the path to the frontend build directory
# In production (Railway), the frontend dist is at /app/static or ../frontend/dist
FRONTEND_DIR = None
_candidates = [
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",  # local dev: backend/../frontend/dist
    Path(__file__).resolve().parent.parent / "static",                     # production: backend/static
    Path("/app/static"),                                                   # railway fallback
]
for candidate in _candidates:
    if candidate.is_dir() and (candidate / "index.html").exists():
        FRONTEND_DIR = candidate
        break


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    if FRONTEND_DIR:
        logger.info("Serving frontend from: %s", FRONTEND_DIR)
    else:
        logger.info("No frontend build found — API-only mode.")
    logger.info("VOCA API is ready.")
    yield
    logger.info("VOCA API shutting down.")


app = FastAPI(
    title="VOCA API",
    description="Voice-Operated Command Assistant — Your Voice. Your Actions.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if settings.CORS_ORIGINS:
    cors_origins.extend(settings.CORS_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(cors_origins)),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|.*\.up\.railway\.app)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers (must come BEFORE the static file mount)
app.include_router(voice_router)
app.include_router(expenses_router)
app.include_router(tasks_router)
app.include_router(reminders_router)
app.include_router(dashboard_router)
app.include_router(history_router)
app.include_router(analytics_router)
app.include_router(contacts_router)
app.include_router(emails_router)
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    gemini_status = "configured" if settings.GEMINI_API_KEY else "not configured"
    return {
        "status": "healthy",
        "service": "VOCA API",
        "version": "1.0.0",
        "gemini": gemini_status,
        "frontend": "served" if FRONTEND_DIR else "not available",
    }


# ---------------------------------------------------------------------------
# Serve the React frontend (SPA) from the built dist folder
# ---------------------------------------------------------------------------
if FRONTEND_DIR:
    # Mount static assets (JS, CSS, images) at /assets
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")

    # Catch-all: serve index.html for any non-API route (SPA client-side routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """Serve the React SPA — returns index.html for all non-API routes."""
        # Try to serve the exact file first (e.g., favicon.ico)
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for client-side routing
        return FileResponse(str(FRONTEND_DIR / "index.html"))
else:
    @app.get("/")
    async def root():
        """Root endpoint when no frontend is available."""
        return {
            "message": "VOCA API is running!",
            "documentation": "/docs",
            "health": "/health",
            "status": "healthy",
        }
