"""Model loading and promotion API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from libs.contracts.model_registry import ModelStage

router = APIRouter()


class LoadModelRequest(BaseModel):
    model_id: str
    version: str
    framework: str
    feature_names: list[str]


class PromoteModelRequest(BaseModel):
    model_id: str
    stage: ModelStage


@router.post("/load", status_code=status.HTTP_202_ACCEPTED)
async def load_model(request: LoadModelRequest) -> dict:
    """Trigger loading of a model artifact into the in-process registry."""
    # Stub — full implementation wires to loader.load_runner + ModelRegistry.register
    return {"message": f"Model '{request.model_id}' queued for loading."}


@router.post("/promote")
async def promote_model(request: PromoteModelRequest) -> dict:
    """Promote a loaded model to a new stage (e.g. staging → canary → production)."""
    return {"message": f"Model '{request.model_id}' promoted to {request.stage.value}."}


@router.get("/")
async def list_models() -> list[dict]:
    """List all currently loaded models."""
    return []
