"""Model loader: deserialise artifacts from the artifact store into runners."""
from __future__ import annotations

from libs.common.exceptions import ModelLoadError
from libs.contracts.model_registry import ModelFramework, ModelRecord
from libs.storage.artifact_store import ArtifactStore


def load_runner(record: ModelRecord, store: ArtifactStore | None = None):
    """Load the appropriate runner for *record*.

    Returns an ``XGBRunner``, ``ONNXRunner``, or ``TorchRunner`` depending on
    ``record.framework``.

    Raises:
        ModelLoadError: If the artifact cannot be loaded.
    """
    store = store or ArtifactStore()

    try:
        if record.framework == ModelFramework.XGBOOST:
            from libs.models.xgb_runner import XGBRunner
            return XGBRunner.from_artifact(record, store)

        if record.framework == ModelFramework.ONNX:
            from libs.models.onnx_runner import ONNXRunner
            return ONNXRunner.from_artifact(record, store)

        if record.framework == ModelFramework.PYTORCH:
            from libs.models.torch_runner import TorchRunner
            return TorchRunner.from_artifact(record, store)

    except Exception as exc:
        raise ModelLoadError(
            f"Failed to load model '{record.id}' ({record.framework.value}): {exc}"
        ) from exc

    raise ModelLoadError(f"Unsupported framework: {record.framework.value}")
