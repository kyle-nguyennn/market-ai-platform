"""P2 strategy control tests, including causal prefix invariance."""
import numpy as np
import pandas as pd
import pytest

from competitions.alphanova.research.positions import position_policy, policy_diagnostics


def targets(seed=1, n=160):
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(rng.normal(size=(n, 20)))
    return frame.sub(frame.mean(axis=1), axis=0)


@pytest.mark.parametrize("band,fraction", [
    (0.0, 1.0),
    (0.1, 1.0),
    (3.0, 1.0),
    (0.1, 0.25),
])
def test_market_neutral_prefix_and_repeatable(band, fraction):
    x = targets()
    a = position_policy(x, band, fraction)
    b = position_policy(x.iloc[:67], band, fraction)
    np.testing.assert_allclose(a.iloc[:67].values, b.values)
    np.testing.assert_allclose(a.values, position_policy(x, band, fraction).values)
    assert np.max(np.abs(a.mean(axis=1))) < 1e-10
    assert np.isfinite(a.values).all()


def test_zero_band_full_rebalance_is_identity():
    frame = targets()
    np.testing.assert_allclose(
        position_policy(frame, 0, 1).to_numpy(),
        frame.to_numpy(),
        atol=1e-12,
    )


def test_band_reduces_turnover_on_small_changes():
    rng = np.random.default_rng(7)
    x = np.cumsum(rng.normal(scale=0.0005, size=(100, 20)), axis=0)
    frame = pd.DataFrame(x)
    frame = frame.sub(frame.mean(axis=1), axis=0)
    no_band = position_policy(frame)
    with_band = position_policy(frame, min_trade_l1=0.02)
    def turnover(p):
        return float(np.abs(np.diff(p.to_numpy(), axis=0)).sum())
    assert turnover(with_band) <= turnover(no_band) + 1e-10
    assert policy_diagnostics(with_band)["rebalance_count"] < 99


@pytest.mark.parametrize("band,fraction", [(-1, 1), (0, 0), (0, 1.01)])
def test_invalid_policy_parameters(band, fraction):
    with pytest.raises(ValueError):
        position_policy(targets(), band, fraction)
