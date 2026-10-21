"""Import smoke tests for research namespaces added by the first scaffold."""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "libs.features.microstructure",
        "libs.features.volatility",
        "libs.features.cross_sectional",
        "libs.features.technical",
        "libs.signals",
        "libs.signals.momentum",
        "libs.signals.mean_reversion",
        "libs.signals.order_flow",
        "libs.signals.ml",
        "libs.strategies",
        "libs.strategies.market_making",
        "libs.strategies.statistical_arbitrage",
        "libs.strategies.portfolio",
        "libs.strategies.competition",
        "libs.strategies.competition.alphanova",
        "libs.backtesting",
    ],
)
def test_namespace_is_importable(module: str) -> None:
    assert importlib.import_module(module).__path__
