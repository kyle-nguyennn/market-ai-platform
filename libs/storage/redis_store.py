"""Redis store for online feature cache with TTL management."""
from __future__ import annotations

import json
from typing import Any

import redis

from libs.common.settings import get_settings


class RedisStore:
    """Key-value store backed by Redis with JSON serialisation."""

    def __init__(self, url: str | None = None) -> None:
        url = url or get_settings().redis_url
        self._client: redis.Redis = redis.Redis.from_url(url, decode_responses=True)

    # --- Feature cache ---

    def set_features(
        self,
        entity_id: str,
        features: dict[str, Any],
        ttl_seconds: int = 3600,
    ) -> None:
        """Write a feature snapshot for *entity_id* with an expiry."""
        key = self._feature_key(entity_id)
        self._client.set(key, json.dumps(features), ex=ttl_seconds)

    def get_features(self, entity_id: str) -> dict[str, Any] | None:
        """Read the cached feature snapshot for *entity_id*, or None if absent."""
        key = self._feature_key(entity_id)
        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def delete_features(self, entity_id: str) -> None:
        self._client.delete(self._feature_key(entity_id))

    # --- Generic helpers ---

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        serialised = json.dumps(value)
        if ttl_seconds:
            self._client.set(key, serialised, ex=ttl_seconds)
        else:
            self._client.set(key, serialised)

    def get(self, key: str) -> Any | None:
        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def healthcheck(self) -> bool:
        try:
            return self._client.ping()
        except redis.RedisError:
            return False

    @staticmethod
    def _feature_key(entity_id: str) -> str:
        return f"features:{entity_id}"
