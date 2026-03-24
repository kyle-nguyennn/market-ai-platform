"""Scoring API endpoint."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from libs.common.exceptions import InferenceError, ModelNotFoundError

router = APIRouter()


class ScoreRequest(BaseModel):
    model_name: str
    entity_id: str
    features: dict[str, float]


class ScoreResponse(BaseModel):
    entity_id: str
    model_name: str
    score: float
    label: int
    from_cache: bool = False
    model_slot: str = "production"


@router.post("/", response_model=ScoreResponse)
async def score(request: ScoreRequest) -> ScoreResponse:
    """Score a single entity using the named production model."""
    # Stub implementation — wire to Router + ModelRegistry in full build.
    raise HTTPException(
        status_code=503,
        detail=f"No model loaded for '{request.model_name}'. Load a model first.",
    )


@router.post("/batch", response_model=list[ScoreResponse])
async def score_batch(requests: list[ScoreRequest]) -> list[ScoreResponse]:
    """Score a batch of entities."""
    raise HTTPException(status_code=503, detail="Batch scoring not yet configured.")
