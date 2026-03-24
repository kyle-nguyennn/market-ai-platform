"""Prediction cache backed by Redis with TTL and cache-aside pattern."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from libs.storage.redis_store import RedisStore


class PredictionCache:
    """Cache inference results keyed on a hash of the input features."""

    _PREFIX = "pred_cache:"

    def __init__(self, store: RedisStore | None = None, ttl_seconds: int = 300) -> None:
        self._store = store or RedisStore()
        self.ttl_seconds = ttl_seconds

    def _key(self, model_id: str, features: dict) -> str:
        payload = json.dumps({"model": model_id, "features": features}, sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return f"{self._PREFIX}{model_id}:{digest}"

    def get(self, model_id: str, features: dict) -> Any | None:
        """Return a cached prediction or None on cache miss."""
        return self._store.get(self._key(model_id, features))

    def set(self, model_id: str, features: dict, prediction: Any) -> None:
        """Store a prediction with the configured TTL."""
        self._store.set(self._key(model_id, features), prediction, self.ttl_seconds)

    def invalidate(self, model_id: str, features: dict) -> None:
        key = self._key(model_id, features)
        self._store._client.delete(key)
