"""Pydantic contracts for dataset objects."""
from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DataTier(StrEnum):
    RAW = "raw"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class DatasetStatus(StrEnum):
    PENDING = "pending"
    BUILDING = "building"
    READY = "ready"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class DatasetSpec(BaseModel):
    name: str
    version: str
    description: str = ""
    tier: DataTier = DataTier.GOLD
    start_date: date
    end_date: date
    universe: list[str] = Field(default_factory=list)
    feature_names: list[str] = Field(default_factory=list)
    label_name: str | None = None
    partition_cols: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class DatasetRecord(BaseModel):
    id: str
    spec: DatasetSpec
    status: DatasetStatus = DatasetStatus.PENDING
    artifact_path: str | None = None
    row_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
