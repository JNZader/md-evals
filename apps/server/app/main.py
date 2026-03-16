"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.eval import router as eval_router
from app.routes.providers import router as providers_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    # Startup — create tables in dev mode (use Alembic in production)
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Dev mode: database tables created/verified")

    yield

    # Shutdown — dispose engine
    await engine.dispose()
    logger.info("Database engine disposed")


app = FastAPI(
    title="md-evals API",
    version="0.1.0",
    description="Web API for md-evals skill evaluation framework",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth_router)
app.include_router(providers_router)
app.include_router(eval_router)


# --- Health ---
@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
    }
