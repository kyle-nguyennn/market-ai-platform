"""eval-control-plane service entry point."""
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
    logger.info("eval_control_plane_starting", port=settings.eval_control_plane_port)
    yield
    logger.info("eval_control_plane_shutdown")


app = FastAPI(
    title="Eval Control Plane",
    description="Model evaluation orchestration, drift monitoring, and promotion decisions.",
    version="0.1.0",
    lifespan=lifespan,
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

from services.eval_control_plane.app.api import runs, drift, promotions  # noqa: E402

app.include_router(runs.router, prefix="/eval/runs", tags=["eval-runs"])
app.include_router(drift.router, prefix="/eval/drift", tags=["drift"])
app.include_router(promotions.router, prefix="/eval/promotions", tags=["promotions"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "eval-control-plane"}
