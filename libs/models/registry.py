"""In-memory model registry: track and promote loaded models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from libs.common.exceptions import ModelNotFoundError
from libs.contracts.model_registry import ModelStage


@dataclass
class ModelEntry:
    id: str
    name: str
    version: str
    stage: ModelStage
    runner: Any  # an XGBRunner, ONNXRunner, etc.


class ModelRegistry:
    """Thread-safe in-process registry of loaded model runners."""

    def __init__(self) -> None:
        self._models: dict[str, ModelEntry] = {}  # keyed by model.id

    def register(self, entry: ModelEntry) -> None:
        self._models[entry.id] = entry

    def get(self, model_id: str) -> ModelEntry:
        entry = self._models.get(model_id)
        if entry is None:
            raise ModelNotFoundError(f"Model '{model_id}' is not loaded in the registry.")
        return entry

    def get_by_stage(self, name: str, stage: ModelStage) -> ModelEntry:
        for entry in self._models.values():
            if entry.name == name and entry.stage == stage:
                return entry
        raise ModelNotFoundError(f"No {stage.value} model found for '{name}'.")

    def promote(self, model_id: str, stage: ModelStage) -> None:
        entry = self.get(model_id)
        entry.stage = stage

    def list_all(self) -> list[ModelEntry]:
        return list(self._models.values())
