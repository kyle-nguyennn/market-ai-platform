"""ONNX Runtime model runner."""
from __future__ import annotations

from typing import Any

import numpy as np

from libs.contracts.model_registry import ModelRecord
from libs.storage.artifact_store import ArtifactStore


class ONNXRunner:
    """Runs inference using an ONNX Runtime session."""

    def __init__(self, session, input_name: str, feature_names: list[str]) -> None:
        self._session = session
        self._input_name = input_name
        self.feature_names = feature_names

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        values = np.array(
            [features.get(f, 0.0) for f in self.feature_names],
            dtype=np.float32,
        ).reshape(1, -1)
        outputs = self._session.run(None, {self._input_name: values})
        score = float(outputs[0].flatten()[0])
        return {"score": score, "label": int(score >= 0.5)}

    @classmethod
    def from_artifact(cls, record: ModelRecord, store: ArtifactStore) -> ONNXRunner:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise ImportError("onnxruntime is required for ONNXRunner.") from exc

        path = store.artifact_path(record.id, record.version, "model.onnx")
        session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        input_name = session.get_inputs()[0].name
        feature_names = record.params.get("feature_names", [])
        return cls(session, input_name, feature_names)
