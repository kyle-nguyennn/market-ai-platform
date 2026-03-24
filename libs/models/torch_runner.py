"""PyTorch model runner stub — optional component."""
from __future__ import annotations

from typing import Any

from libs.contracts.model_registry import ModelRecord
from libs.storage.artifact_store import ArtifactStore


class TorchRunner:
    """Runs inference using a ``torch.nn.Module`` loaded from a state-dict file."""

    def __init__(self, model, feature_names: list[str]) -> None:
        self._model = model
        self.feature_names = feature_names

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        try:
            import torch
        except ImportError as exc:
            raise ImportError("PyTorch is required for TorchRunner.") from exc

        values = [features.get(f, 0.0) for f in self.feature_names]
        tensor = torch.tensor(values, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            output = self._model(tensor)
        score = float(output.squeeze().sigmoid().item())
        return {"score": score, "label": int(score >= 0.5)}

    @classmethod
    def from_artifact(cls, record: ModelRecord, store: ArtifactStore) -> TorchRunner:
        try:
            import torch  # noqa: F401  # TODO: use torch.load for state dict
        except ImportError as exc:
            raise ImportError("PyTorch is required for TorchRunner.") from exc

        state = store.load(record.id, record.version, filename="model.pt")  # noqa: F841
        # TODO: load state dict into model architecture from record.params
        raise NotImplementedError(
            "TorchRunner.from_artifact requires model architecture"
            " to be provided via record.params."
        )
