from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from routers import articles, episodes
from store import Store

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
)
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    os.makedirs(os.path.join(settings.storage_path, "episodes"), exist_ok=True)
    app.state.store = Store(db_path=os.path.join(settings.storage_path, "signal.db"))
    log.info("startup", storage_path=settings.storage_path)
    yield
    log.info("shutdown")


app = FastAPI(title="The Signal", version="0.1.0", lifespan=lifespan)

@app.middleware("http")
async def require_api_token(request: Request, call_next):
    """Protect the API and media files when SIGNAL_API_TOKEN is configured.

    Accepts `Authorization: Bearer <token>` or `?token=` (for <audio> tags,
    which cannot send headers). /health stays open. OPTIONS passes through:
    CORS preflights carry no auth header by design.
    """
    token = get_settings().signal_api_token
    path = request.url.path
    if (
        token
        and request.method != "OPTIONS"
        and (path.startswith("/api") or path.startswith("/data"))
    ):
        auth = request.headers.get("authorization", "")
        provided = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        provided = provided or request.query_params.get("token") or ""
        if not secrets.compare_digest(provided, token):
            return JSONResponse(
                {"detail": "Invalid or missing API token"}, status_code=401
            )
    return await call_next(request)


# Added after the auth middleware so CORS wraps it: preflights are answered
# and even 401 responses carry CORS headers the browser will surface.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(articles.router)
app.include_router(episodes.router)

settings = get_settings()
os.makedirs(settings.storage_path, exist_ok=True)
app.mount("/data", StaticFiles(directory=settings.storage_path), name="data")


@app.get("/health")
async def health():
    s = get_settings()
    return {
        "status": "ok",
        "anthropic_configured": bool(s.anthropic_api_key),
        "elevenlabs_configured": bool(s.elevenlabs_api_key),
    }
