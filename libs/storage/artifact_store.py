"""Artifact store — save and load ML model artifacts from the filesystem."""
from __future__ import annotations

import io
import os
import pickle
from pathlib import Path
from typing import Any

from libs.common.settings import get_settings


class ArtifactStore:
    """Local filesystem artifact store.

    Files are stored at::

        {root}/{model_id}/{version}/model.pkl   (or .ubj for XGBoost, etc.)
    """

    def __init__(self, root: str | Path | None = None) -> None:
        settings = get_settings()
        self.root = Path(root or settings.artifact_root)

    def artifact_path(self, model_id: str, version: str, filename: str) -> Path:
        return self.root / model_id / version / filename

    def save(
        self,
        obj: Any,
        model_id: str,
        version: str,
        filename: str = "model.pkl",
    ) -> Path:
        """Serialise *obj* with pickle and write to the artifact store.

        Returns the path of the saved file.
        """
        dest = self.artifact_path(model_id, version, filename)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
        return dest

    def load(
        self,
        model_id: str,
        version: str,
        filename: str = "model.pkl",
    ) -> Any:
        """Load and return the artifact at the given coordinates."""
        path = self.artifact_path(model_id, version, filename)
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: {path}")
        with path.open("rb") as fh:
            return pickle.load(fh)  # noqa: S301 — trusted internal artifacts only

    def exists(self, model_id: str, version: str, filename: str = "model.pkl") -> bool:
        return self.artifact_path(model_id, version, filename).exists()

    def list_versions(self, model_id: str) -> list[str]:
        model_dir = self.root / model_id
        if not model_dir.exists():
            return []
        return sorted(
            d.name for d in model_dir.iterdir() if d.is_dir()
        )
