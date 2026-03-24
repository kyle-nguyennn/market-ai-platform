"""Feature registry: maps feature names to compute functions."""
from __future__ import annotations

from collections.abc import Callable

import polars as pl

from libs.common.exceptions import FeatureNotFoundError

# Type alias for a feature compute function.
FeatureFn = Callable[[pl.DataFrame], pl.Series]

_registry: dict[str, FeatureFn] = {}


def register(name: str) -> Callable[[FeatureFn], FeatureFn]:
    """Decorator to register a feature compute function under *name*.

    Example::

        @register("ret_1d")
        def ret_1d(df: pl.DataFrame) -> pl.Series:
            return df["close"].pct_change().alias("ret_1d")
    """
    def decorator(fn: FeatureFn) -> FeatureFn:
        _registry[name] = fn
        return fn
    return decorator


def compute(name: str, df: pl.DataFrame) -> pl.Series:
    """Compute the named feature from *df*.

    Raises:
        FeatureNotFoundError: If *name* is not registered.
    """
    if name not in _registry:
        raise FeatureNotFoundError(f"Feature '{name}' is not registered.")
    return _registry[name](df)


def list_features() -> list[str]:
    """Return a sorted list of all registered feature names."""
    return sorted(_registry)
