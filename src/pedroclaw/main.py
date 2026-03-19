"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pedroclaw.config import settings
from pedroclaw.dashboard.router import router as dashboard_router
from pedroclaw.knowledge.store import init_db
from pedroclaw.webhooks.router import router as webhooks_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Pedroclaw starting", version="0.1.0", review_engine=settings.review_engine)
    await init_db()
    yield
    logger.info("Pedroclaw shutting down")


app = FastAPI(
    title="Pedroclaw",
    description="Workflow Claw — AI-powered GitLab pipeline automation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

# Serve frontend static files if built
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
