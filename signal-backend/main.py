from __future__ import annotations

import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
