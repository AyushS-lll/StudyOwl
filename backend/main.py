"""
StudyOwl — FastAPI application entry point.
Registers all routers and configures CORS, lifespan, and middleware.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db import init_db
from routers import sessions, alerts, progress, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise DB connection pool on startup, close on shutdown."""
    await init_db()
    yield


app = FastAPI(
    title="StudyOwl API",
    version="0.1.0",
    description="AI-powered homework assistant — Socratic hints, never spoilers.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix="/api/auth",     tags=["auth"])
app.include_router(sessions.router, prefix="/api/session",  tags=["sessions"])
app.include_router(progress.router, prefix="/api/student",  tags=["progress"])
app.include_router(alerts.router,   prefix="/api/alert",    tags=["alerts"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "studyowl-api"}
