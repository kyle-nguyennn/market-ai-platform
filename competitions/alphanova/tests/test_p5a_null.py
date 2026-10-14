"""P5-A synthetic null calibration tests."""
from __future__ import annotations

import numpy as np
import pytest

from competitions.alphanova.research.run_p5a_null import block_null


def test_known_factor_beats_null_and_is_deterministic():
    rng = np.random.default_rng(44)
    x = rng.normal(size=(840, 20))
    y = 0.3 * x + rng.normal(0, .1, size=x.shape)
    a = block_null(x, y, block_rows=24, permutations=59, seed=4, chunks=7)
    b = block_null(x, y, block_rows=24, permutations=59, seed=4, chunks=7)
    assert a == b
    assert a["observed_ic"] > .9
    assert a["empirical_p_ic"] <= .05
    assert a["observed_beta"] == pytest.approx(.3, abs=.01)
    assert a["beta_sign_fraction"] == 1.0


def test_trim_prefix_only_for_equal_blocks():
    rng = np.random.default_rng(5)
    x, y = rng.normal(size=(101, 20)), rng.normal(size=(101, 20))
    a = block_null(x, y, block_rows=10, permutations=19, seed=8)
    b = block_null(x[1:], y[1:], block_rows=10, permutations=19, seed=8)
    assert a == b
    assert a["n_training_rows"] == 100


def test_invalid_inputs():
    x = np.ones((160, 20))
    with pytest.raises(ValueError):
        block_null(x, x[:, :19], block_rows=8, permutations=19, seed=1)
    with pytest.raises(ValueError):
        block_null(x, x, block_rows=10, permutations=3, seed=1)
