"""Pydantic contracts for evaluation specifications and results."""
from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class SliceSpec(BaseModel):
    name: str
    filters: dict[str, Any]


class DriftConfig(BaseModel):
    psi_threshold: float = 0.2
    ks_threshold: float = 0.1
    reference_window_days: int = 90
    current_window_days: int = 30


class EvalSpec(BaseModel):
    name: str
    model_id: str
    dataset_id: str
    start_date: date
    end_date: date
    slices: list[SliceSpec] = Field(default_factory=list)
    drift: DriftConfig = Field(default_factory=DriftConfig)
    regression_guards: dict[str, float] = Field(default_factory=dict)


class EvalMetric(BaseModel):
    name: str
    value: float
    slice_name: str = "overall"


class EvalRunRecord(BaseModel):
    id: str
    spec: EvalSpec
    status: str = "pending"
    metrics: list[EvalMetric] = Field(default_factory=list)
    passed: bool | None = None
    created_at: str | None = None
    finished_at: str | None = None
