"""dataset-platform service entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from libs.common.logging import configure_logging, get_logger
from libs.common.settings import get_settings

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("dataset_platform_starting", port=settings.dataset_platform_port)
    yield
    logger.info("dataset_platform_shutdown")


app = FastAPI(
    title="Dataset Platform",
    description="Dataset registration, versioning, and quality reporting.",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

from services.dataset_platform.app.api import datasets, features, quality  # noqa: E402

app.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
app.include_router(features.router, prefix="/features", tags=["features"])
app.include_router(quality.router, prefix="/quality", tags=["quality"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "dataset-platform"}
