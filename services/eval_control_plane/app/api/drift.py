"""Drift alert API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException  # noqa: F401  # TODO: validate alert payloads
from pydantic import BaseModel

router = APIRouter()


class DriftAlert(BaseModel):
    alert_id: str
    model_id: str
    feature: str | None = None
    psi: float | None = None
    ks_statistic: float | None = None
    threshold_exceeded: str
    created_at: str


_alerts: list[DriftAlert] = []


@router.get("/alerts", response_model=list[DriftAlert])
async def list_drift_alerts(model_id: str | None = None) -> list[DriftAlert]:
    if model_id:
        return [a for a in _alerts if a.model_id == model_id]
    return _alerts


@router.post("/alerts", response_model=DriftAlert, status_code=201)
async def create_drift_alert(alert: DriftAlert) -> DriftAlert:
    _alerts.append(alert)
    return alert
