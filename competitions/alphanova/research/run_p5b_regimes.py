"""P5-B: frozen regime hypotheses vs constant rank1 benchmark.

Two simple training-only regime models are evaluated on the fixed P4
discovery and confirmation sets; no validation labels are used in fitting.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from competitions.alphanova.research.diagnostics import (
    assert_valid_predictions, pnl_components, summarize,
)
from competitions.alphanova.research.run_feature_screen import (
    summarize_factors, validation_prediction,
)
from competitions.alphanova.research.regime import (
    REGIMES, predict_raw, train_from_panels,
)

# ruff: noqa: I001
ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "external" / "alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))
from data_loader import load_period  # noqa: E402


def analyze_period(period: str, data_dir: Path, config: dict, phase: str) -> list[dict]:
    data = load_period(period, str(data_dir))
    features, target, returns = data["features"], data["target"], data["returns"]
    n_val = min(800, int(0.2 * len(features)))
    n_train = len(features) - n_val
    train_x = features.iloc[:n_train]
    train_y = target.iloc[:n_train]
    val_x = features.iloc[n_train:]
    rows = []
    for regime in REGIMES:
        model = train_from_panels(
            train_x, train_y, regime=regime,
            tail_rows=int(config["train_tail_rows"]),
            embargo_rows=int(config["embargo_rows"]),
            shrinkage=float(config["shrinkage"]),
        )
        factor, tickers = predict_raw(val_x, model)
        val_returns = returns.iloc[n_train:].reindex(columns=tickers)
        positions = validation_prediction(
            factor, 1.0, val_returns.index, tickers,
            int(config["span"]), float(config["trade_band"]),
            float(config["rebalance_fraction"]),
        )
        assert_valid_predictions(positions, val_returns)
        pnl = pnl_components(positions, val_returns)
        row = {
            "phase": phase, "period": period,
            "name": regime, "family": "conditional_rank1",
            "train_rows": n_train - int(config["embargo_rows"]),
            "val_rows": n_val,
            "global_beta": model.beta_global,
            "low_beta": model.beta_low,
            "high_beta": model.beta_high,
            "regime_threshold": model.threshold,
            "train_low_fraction": model.train_low_fraction,
            "signed_target_ic": 0.0,
        }
        # PnL objective deliberately avoids using validation targets.
        row.update(summarize(pnl))
        for col in ("gross", "net"):
            v = pnl[col].to_numpy(dtype=float)
            row[f"sum_{col}"] = float(v.sum())
            row[f"sumsq_{col}"] = float(np.dot(v, v))
        rows.append(row)
    print(f"[P5-B {phase} {period}] evaluated={len(rows)}", flush=True)
    return rows


def run(config: dict, data_dir: Path, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    discovery = config["discovery_periods"]
    confirmation = config["confirmation_periods"]
    if not discovery or not confirmation or max(discovery) >= min(confirmation):
        raise ValueError("Chronological discovery/confirmation split required")
    discovery_rows = [
        item for p in discovery for item in analyze_period(p, data_dir, config, "discovery")
    ]
    # Fixed models/hyperparameters — confirmation does not select settings.
    confirmation_rows = [
        item for p in confirmation
        for item in analyze_period(p, data_dir, config, "confirmation")
    ]
    early = summarize_factors(discovery_rows)
    late = summarize_factors(confirmation_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(discovery_rows).to_csv(
        output_dir / "regime_discovery_per_period.csv", index=False
    )
    pd.DataFrame(confirmation_rows).to_csv(
        output_dir / "regime_confirmation_per_period.csv", index=False
    )
    early.to_csv(output_dir / "regime_discovery_summary.csv", index=False)
    late.to_csv(output_dir / "regime_confirmation_summary.csv", index=False)
    (output_dir / "manifest.json").write_text(json.dumps({
        **config,
        "variants": list(REGIMES),
        "note": (
            "Training fits and regime thresholds use earlier labels only. "
            "Confirmation dates were previously researched in P0-P4; "
            "this is not an untouched final test."
        ),
    }, indent=2) + "\n")
    for phase, frame in (("discovery", early), ("confirmation", late)):
        print(f"\nP5-B {phase}:")
        print(frame[["name", "gross_sharpe", "net_sharpe", "positive_periods"]]
              .to_string(index=False), flush=True)
    return early, late


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "competitions/alphanova/configs/p5b_regimes.json",
    )
    parser.add_argument("--data-dir", type=Path, default=KIT / "data/train")
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "competitions/alphanova/results/p5b",
    )
    args = parser.parse_args()
    run(json.loads(args.config.read_text()), args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()
