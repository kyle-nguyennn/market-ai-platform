"""inference-gateway service entry point."""
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
    logger.info("inference_gateway_starting", port=settings.inference_gateway_port)
    yield
    logger.info("inference_gateway_shutdown")


app = FastAPI(
    title="Inference Gateway",
    description="Low-latency scoring endpoint with canary routing and prediction caching.",
    version="0.1.0",
    lifespan=lifespan,
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

from services.inference_gateway.app.api import score, models  # noqa: E402

app.include_router(score.router, prefix="/score", tags=["score"])
app.include_router(models.router, prefix="/models", tags=["models"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "inference-gateway"}
