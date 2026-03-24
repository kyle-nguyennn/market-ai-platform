"""Shadow mode: mirror live traffic to a challenger model without serving its output."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from libs.common.logging import get_logger

logger = get_logger(__name__)


class ShadowRunner:
    """Runs a shadow model alongside the production model.

    The shadow's predictions are logged for offline comparison but never
    returned to the caller.

    Args:
        shadow_fn: Callable that accepts a feature dict and returns a prediction.
        log_fn: Optional async callable to persist shadow predictions (e.g. to a
                queue or database).  Receives ``(entity_id, features, prediction)``.
    """

    def __init__(
        self,
        shadow_fn: Callable[[dict], Any],
        log_fn: Callable[[str, dict, Any], None] | None = None,
    ) -> None:
        self._shadow_fn = shadow_fn
        self._log_fn = log_fn

    async def fire(self, entity_id: str, features: dict) -> None:
        """Asynchronously run the shadow model; errors are swallowed."""
        try:
            prediction = await asyncio.to_thread(self._shadow_fn, features)
            if self._log_fn:
                await asyncio.to_thread(self._log_fn, entity_id, features, prediction)
            logger.debug("shadow_prediction", entity_id=entity_id, prediction=prediction)
        except Exception as exc:
            logger.warning("shadow_model_error", entity_id=entity_id, error=str(exc))
