"""P5-A: approximate training-only shuffled-label null diagnostics.

Not the proprietary AlphaNova gate. Synchronously shuffle whole target
blocks across timestamps to destroy feature-target alignment while keeping
cross-asset structure and within-block target autocorrelation. All data is
strictly from the available training slice, excluding the embargo.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from competitions.alphanova.research.feature_screen import (
    cross_sectional_ic,
    factor_values,
    feature_panels,
    train_linear_slope,
)

# ruff: noqa: I001
ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "external" / "alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))
from data_loader import load_period  # noqa: E402


def finite_average(values: np.ndarray) -> float:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    return float(x.mean()) if x.size else 0.0


def block_null(
    factor: np.ndarray,
    target: np.ndarray,
    *,
    block_rows: int,
    permutations: int,
    seed: int,
    chunks: int = 8,
) -> dict:
    """Two-sided block permutation test for mean training cross-sectional IC.

    For exact equal blocks, discard only a short prefix and retain the most
    recent samples. Shuffling synchronized target row-blocks preserves each
    target cross-section and within-block autocorrelation. The observed
    statistic and every null statistic use exactly the same window.
    """
    if factor.ndim != 2 or factor.shape != target.shape:
        raise ValueError("Factor/target must be matching 2D panels")
    if block_rows < 2 or permutations < 9 or chunks < 2:
        raise ValueError("Invalid null-test parameters")
    total = (len(factor) // block_rows) * block_rows
    if total < block_rows * max(chunks, 3):
        raise ValueError("Insufficient training blocks")
    x = factor[-total:]
    y = target[-total:]
    observed_ic = finite_average(cross_sectional_ic(x, y))
    observed_beta = train_linear_slope(x, y, len(x), len(x))
    n_blocks = total // block_rows
    y_blocks = y.reshape(n_blocks, block_rows, y.shape[1])
    rng = np.random.default_rng(seed)
    null_ics = np.empty(permutations)
    null_betas = np.empty(permutations)
    for j in range(permutations):
        order = rng.permutation(n_blocks)
        shifted_target = y_blocks[order].reshape(y.shape)
        null_ics[j] = finite_average(cross_sectional_ic(x, shifted_target))
        null_betas[j] = train_linear_slope(
            x, shifted_target, len(x), len(x)
        )
    # Empirical p-values are discrete and are NOT AlphaNova gate p-values.
    p_ic = (1 + int((np.abs(null_ics) >= abs(observed_ic)).sum())) / (
        permutations + 1
    )
    p_beta = (1 + int((np.abs(null_betas) >= abs(observed_beta)).sum())) / (
        permutations + 1
    )
    block_indices = np.array_split(np.arange(len(x)), chunks)
    chunk_beta = [
        train_linear_slope(x[ids], y[ids], len(ids), len(ids))
        for ids in block_indices
    ]
    consistent = float(np.mean(
        np.sign(chunk_beta) == np.sign(observed_beta)
    ))
    return {
        "observed_ic": observed_ic,
        "observed_beta": observed_beta,
        "null_ic_mean": float(null_ics.mean()),
        "null_ic_std": float(null_ics.std(ddof=1)),
        "null_ic_q025": float(np.quantile(null_ics, 0.025)),
        "null_ic_q975": float(np.quantile(null_ics, 0.975)),
        "null_beta_std": float(null_betas.std(ddof=1)),
        "empirical_p_ic": float(p_ic),
        "empirical_p_beta": float(p_beta),
        "beta_sign_fraction": consistent,
        "chunk_betas": [float(v) for v in chunk_beta],
        "n_training_rows": total,
        "n_blocks": n_blocks,
        "permutations": permutations,
        "block_rows": block_rows,
    }


def analyze_period(period: str, directory: Path, config: dict) -> dict:
    data = load_period(period, str(directory))
    features, target = data["features"], data["target"]
    n_validation = min(800, int(len(features) * 0.2))
    cutoff = len(features) - n_validation - int(config["embargo_rows"])
    if cutoff < 0:
        raise ValueError("Insufficient history")
    tail = int(config["train_tail_rows"])
    start = max(0, cutoff - tail)
    # No validation features or target rows are accessed by the diagnostic.
    train_features = features.iloc[start:cutoff]
    train_target = target.iloc[start:cutoff]
    raw, tickers = feature_panels(train_features)
    name = str(config["factor"])
    signal = factor_values(name, raw)
    labels = train_target.reindex(columns=tickers).to_numpy(dtype=float)
    report = block_null(
        signal, labels,
        block_rows=int(config["block_rows"]),
        permutations=int(config["permutations"]),
        seed=int(config["seed"]) + int(period),
    )
    return {"period": period, "factor": name, **report}


def run(config: dict, directory: Path, output_dir: Path) -> pd.DataFrame:
    results = []
    for period in config["periods"]:
        report = analyze_period(period, directory, config)
        results.append(report)
        print(
            f"[P5-A {period}] IC={report['observed_ic']:+.5f} "
            f"beta={report['observed_beta']:+.5f} "
            f"p_block={report['empirical_p_ic']:.4f} "
            f"chunk_sign={report['beta_sign_fraction']:.2f}",
            flush=True,
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(results)
    frame.to_csv(output_dir / "training_null_per_period.csv", index=False)
    (output_dir / "manifest.json").write_text(json.dumps({
        **config,
        "scope": "training labels only; validation rows and returns not accessed",
        "null_method": "target blocks permuted; synchronized tickers",
        "limitations": [
            "Not an implementation or estimate of the proprietary server gate",
            "Finite permutation resolution",
            "Historical factors already chosen with reused validation data",
            "Blocks assume exchangeable month-scale target alignment under the null",
        ],
    }, indent=2) + "\n")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "competitions/alphanova/configs/p5a_null.json",
    )
    parser.add_argument("--data-dir", type=Path, default=KIT / "data/train")
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "competitions/alphanova/results/p5a",
    )
    args = parser.parse_args()
    run(json.loads(args.config.read_text()), args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()
