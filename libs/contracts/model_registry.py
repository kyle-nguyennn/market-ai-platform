"""Pydantic contracts for model registry objects."""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ModelStage(StrEnum):
    STAGING = "staging"
    CANARY = "canary"
    PRODUCTION = "production"
    RETIRED = "retired"


class ModelFramework(StrEnum):
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    SKLEARN = "sklearn"
    ONNX = "onnx"
    PYTORCH = "pytorch"


class ModelRecord(BaseModel):
    id: str
    name: str
    version: str
    framework: ModelFramework
    stage: ModelStage = ModelStage.STAGING
    artifact_path: str
    dataset_id: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: str | None = None


class DeploymentRecord(BaseModel):
    id: str
    model_id: str
    stage: ModelStage
    traffic_weight: float = Field(ge=0.0, le=1.0, default=1.0)
    deployed_at: str | None = None
    retired_at: str | None = None
