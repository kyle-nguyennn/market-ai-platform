"""Pydantic contracts for the feature store."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FeatureDefinition(BaseModel):
    name: str
    description: str = ""
    dtype: str  # e.g. "float64", "int32"
    group: str = "default"
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class FeatureVector(BaseModel):
    entity_id: str  # e.g. ticker symbol
    as_of: datetime
    features: dict[str, float | int | str | None]


class OnlineFeatureSnapshot(BaseModel):
    entity_id: str
    features: dict[str, float | int | str | None]
    served_at: datetime
    ttl_seconds: int = 3600
