"""XGBoost model runner."""
from __future__ import annotations

from typing import Any

import numpy as np
import xgboost as xgb

from libs.contracts.model_registry import ModelRecord
from libs.storage.artifact_store import ArtifactStore


class XGBRunner:
    """Wraps an ``xgb.Booster`` and exposes a ``predict`` interface."""

    def __init__(self, booster: xgb.Booster, feature_names: list[str]) -> None:
        self._booster = booster
        self.feature_names = feature_names

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        """Return a probability score dict for the given feature map."""
        values = np.array([features.get(f, 0.0) for f in self.feature_names], dtype=np.float32)
        dmatrix = xgb.DMatrix(values.reshape(1, -1), feature_names=self.feature_names)
        proba = float(self._booster.predict(dmatrix)[0])
        return {"score": proba, "label": int(proba >= 0.5)}

    def predict_batch(self, feature_list: list[dict[str, float]]) -> list[dict[str, Any]]:
        rows = np.array(
            [[row.get(f, 0.0) for f in self.feature_names] for row in feature_list],
            dtype=np.float32,
        )
        dmatrix = xgb.DMatrix(rows, feature_names=self.feature_names)
        probas = self._booster.predict(dmatrix)
        return [{"score": float(p), "label": int(p >= 0.5)} for p in probas]

    @classmethod
    def from_artifact(cls, record: ModelRecord, store: ArtifactStore) -> XGBRunner:
        booster = store.load(record.id, record.version, filename="model.ubj")
        feature_names = record.params.get("feature_names", [])
        return cls(booster, feature_names)
