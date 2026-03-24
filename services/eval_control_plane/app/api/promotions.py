"""Model promotion decision API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from libs.contracts.model_registry import ModelStage

router = APIRouter()


class PromotionDecision(BaseModel):
    decision_id: str
    model_id: str
    eval_run_id: str
    from_stage: ModelStage
    to_stage: ModelStage
    approved: bool
    reason: str = ""
    decided_at: str


_decisions: list[PromotionDecision] = []


@router.get("/", response_model=list[PromotionDecision])
async def list_decisions() -> list[PromotionDecision]:
    return _decisions


@router.post("/", response_model=PromotionDecision, status_code=201)
async def record_decision(decision: PromotionDecision) -> PromotionDecision:
    _decisions.append(decision)
    return decision
