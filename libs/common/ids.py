"""ID generation utilities: UUIDs, slug builders, deterministic hash IDs."""
from __future__ import annotations

import hashlib
import uuid


def new_uuid() -> str:
    """Return a new random UUID4 as a lowercase hex string."""
    return str(uuid.uuid4())


def deterministic_id(*parts: str) -> str:
    """Return a stable SHA-256-based ID from ordered string parts.

    Useful for content-addressable keys (dataset versions, feature snapshots).
    """
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def short_id(length: int = 8) -> str:
    """Return a short random alphanumeric ID."""
    return uuid.uuid4().hex[:length]
