"""Fallback strategies for inference failures: last-known-good, default scores."""
from __future__ import annotations

from typing import Any

from libs.common.exceptions import (
    InferenceError,  # noqa: F401  # TODO: raise on fallback exhaustion
)
from libs.storage.redis_store import RedisStore


class FallbackHandler:
    """Serve a stale or default prediction when the primary model fails.

    Strategy priority:
    1. Last-known-good from Redis cache.
    2. Global default score.
    """

    _LAST_GOOD_PREFIX = "last_good:"

    def __init__(
        self,
        store: RedisStore | None = None,
        default_score: float = 0.0,
        ttl_seconds: int = 86_400,
    ) -> None:
        self._store = store or RedisStore()
        self.default_score = default_score
        self.ttl_seconds = ttl_seconds

    def record_good(self, model_id: str, entity_id: str, prediction: Any) -> None:
        """Persist the latest successful prediction as the last-known-good."""
        key = f"{self._LAST_GOOD_PREFIX}{model_id}:{entity_id}"
        self._store.set(key, prediction, self.ttl_seconds)

    def get_fallback(self, model_id: str, entity_id: str) -> Any:
        """Return the last-known-good prediction, or the global default."""
        key = f"{self._LAST_GOOD_PREFIX}{model_id}:{entity_id}"
        cached = self._store.get(key)
        return cached if cached is not None else {"score": self.default_score, "fallback": True}
