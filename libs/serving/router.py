"""Traffic router for canary/shadow inference deployments."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Protocol


class ModelRunner(Protocol):
    def predict(self, features: dict) -> dict: ...


@dataclass
class RouteConfig:
    """Traffic allocation across named model slots."""
    production: str
    canary: str | None = None
    canary_weight: float = 0.0  # fraction [0, 1] sent to canary
    shadow: str | None = None   # receives all traffic but response is discarded


@dataclass
class Router:
    """Route inference requests to the production, canary, or shadow model.

    Args:
        models: Mapping of slot name → ModelRunner.
        config: Traffic split configuration.
    """
    models: dict[str, ModelRunner]
    config: RouteConfig

    def route(self, features: dict) -> tuple[str, dict]:
        """Return (slot_name, prediction) for the authoritative prediction.

        Side-effects: fires shadow prediction if configured.
        """
        # Shadow: always run in parallel (fire-and-forget in production)
        if self.config.shadow and self.config.shadow in self.models:
            try:
                self.models[self.config.shadow].predict(features)
            except Exception:
                pass  # shadow failures are never surfaced

        # Canary: probabilistic split
        if (
            self.config.canary
            and self.config.canary in self.models
            and random.random() < self.config.canary_weight
        ):
            slot = self.config.canary
        else:
            slot = self.config.production

        return slot, self.models[slot].predict(features)
