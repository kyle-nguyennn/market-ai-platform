"""Run P0/P1 diagnostics on the untouched AlphaNova kit.

From repository root:
    python -m competitions.alphanova.research.run_experiments --scope latest
    python -m competitions.alphanova.research.run_experiments --scope full

Run with LFS binary data checked out. Results are written as CSV/JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from competitions.alphanova.research.diagnostics import (
    assert_valid_predictions,
    new_history_slice,
    pnl_components,
    summarize,
)

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "external" / "alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))

from data_loader import list_periods, load_period  # noqa: E402
from walkforward import compute_val_rows  # noqa: E402
from demo_engineered import EngineeredXGBoostPredictor  # noqa: E402
from competitions.alphanova.submissions.ridge_v1 import RidgeCrossSectionalPredictor  # noqa: E402
from competitions.alphanova.submissions.xgb_interactions_v1 import XGBInteractionPredictor  # noqa: E402

REGISTRY = {
    "baseline": EngineeredXGBoostPredictor,
    "ridge": RidgeCrossSectionalPredictor,
    "xgb_interactions": XGBInteractionPredictor,
}


def run(
    data_dir: Path,
    output_dir: Path,
    models: list[str],
    spans: list[int],
    signs: list[int],
    scope: str,
    embargo_rows: int = 0,
) -> list[dict]:
    periods = list_periods(str(data_dir))
    if not periods:
        raise FileNotFoundError(f"No training periods in {data_dir} (fetch Git LFS binaries)")
    if scope == "latest":
        periods = periods[-1:]
    if embargo_rows < 0:
        raise ValueError("embargo_rows must be nonnegative")
    if not all(x in REGISTRY for x in models):
        raise ValueError(f"Unknown model(s): {set(models) - set(REGISTRY)}")
    if not all(x > 0 for x in spans):
        raise ValueError("EWM spans must be positive")
    if not all(x in (-1, 1) for x in signs):
        raise ValueError("Signs must be +1 or -1")

    pnl_by_key = defaultdict(list)
    novel_pnl_by_key = defaultdict(list)
    period_records: list[dict] = []
    timing_by_key = defaultdict(list)
    previous_total: int | None = None

    for period in periods:
        panel = load_period(period, str(data_dir))
        features, target, returns = panel["features"], panel["target"], panel["returns"]
        n_total = len(features)
        n_val = compute_val_rows(n_total)
        n_train = n_total - n_val
        train_end = n_train - embargo_rows
        if n_val < 2 or train_end < 2:
            raise ValueError(f"Period {period}: not enough rows for this embargo")

        train_features = features.iloc[:train_end]
        train_target = target.iloc[:train_end]
        val_features = features.iloc[n_train:]
        val_returns = returns.iloc[n_train:]
        print(f"[{period}] rows={n_total} train={train_end} validation={n_val}")

        for model_name in models:
            cls = REGISTRY[model_name]
            predictor = cls()
            if hasattr(predictor, "generate_features"):
                predictor.generate_features(features)
            t0 = time.monotonic()
            predictor.train(train_features, train_target)
            train_sec = time.monotonic() - t0

            for span in spans:
                predictor.span = span
                t1 = time.monotonic()
                predictions = predictor.predict(val_features)
                pred_sec = time.monotonic() - t1
                assert_valid_predictions(predictions, val_returns)
                for sign in signs:
                    key = (model_name, span, sign)
                    pnl = pnl_components(sign * predictions, val_returns)
                    novel = new_history_slice(pnl, n_train, previous_total)
                    pnl_by_key[key].append(pnl)
                    novel_pnl_by_key[key].append(novel)
                    timing_by_key[key].append((train_sec, pred_sec))

                    item = {
                        "period": period,
                        "model": model_name,
                        "span": span,
                        "sign": sign,
                        "train_seconds": round(train_sec, 4),
                        "predict_seconds": round(pred_sec, 4),
                        "new_history_rows": len(novel),
                    }
                    item.update(summarize(pnl))
                    period_records.append(item)

                    if train_sec > 240 or pred_sec > 60:
                        raise TimeoutError(
                            f"{key} exceeded contest limits: train={train_sec:.1f}s "
                            f"predict={pred_sec:.1f}s"
                        )
        previous_total = n_total

    summary_records: list[dict] = []
    for key, frames in pnl_by_key.items():
        all_pnl = pd.concat(frames, ignore_index=True)
        novel_frames = novel_pnl_by_key[key]
        novel_pnl = pd.concat(novel_frames, ignore_index=True)
        model_name, span, sign = key
        per_period = [x for x in period_records if
                      (x["model"], x["span"], x["sign"]) == key]
        times = timing_by_key[key]
        record = {
            "model": model_name,
            "span": span,
            "sign": sign,
            "scope": scope,
            "embargo_rows": embargo_rows,
            "periods": len(frames),
            "positive_periods": sum(x["net_sharpe"] > 0 for x in per_period),
            "max_train_seconds": max(t[0] for t in times),
            "max_predict_seconds": max(t[1] for t in times),
        }
        record.update(summarize(all_pnl))
        novel_stats = summarize(novel_pnl)
        record.update({f"new_history_{k}": v for k, v in novel_stats.items()})
        summary_records.append(record)

    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(period_records).to_csv(output_dir / "per_period.csv", index=False)
    pd.DataFrame(summary_records).sort_values(
        "net_sharpe", ascending=False
    ).to_csv(output_dir / "summary.csv", index=False)
    manifest = {
        "scope": scope,
        "models": models,
        "spans": spans,
        "signs": signs,
        "period_keys": periods,
        "embargo_rows": embargo_rows,
        "data_dir": str(data_dir),
        "note": (
            "Per-period lag and transaction-cost resets match the official local "
            "runner; new_history metrics trim overlap by cumulative row position, "
            "and are additional diagnostics, not official scores."
        ),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("\n=== Net-Sharpe comparison (local, not a leaderboard result) ===")
    for r in sorted(summary_records, key=lambda x: x["net_sharpe"], reverse=True):
        print(
            f"{r['model']:17s} span={r['span']:3d} sign={r['sign']:+d} "
            f"net={r['net_sharpe']:+.5f} gross={r['gross_sharpe']:+.5f} "
            f"new_history_net={r['new_history_net_sharpe']:+.5f} "
            f"turnover={r['mean_turnover']:.5g}"
        )
    print(f"Saved: {output_dir}")
    return summary_records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("latest", "full"), default="latest")
    parser.add_argument("--config", type=Path, default=ROOT / "competitions/alphanova/configs/p1_grid.json")
    parser.add_argument("--models", nargs="+", choices=tuple(REGISTRY), default=None)
    parser.add_argument("--spans", nargs="+", type=int, default=None)
    parser.add_argument("--signs", nargs="+", type=int, default=None)
    parser.add_argument("--embargo-rows", type=int, default=None)
    parser.add_argument("--data-dir", type=Path, default=KIT / "data/train")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "competitions/alphanova/results")
    args = parser.parse_args()

    config = json.loads(args.config.read_text())
    run(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        models=args.models if args.models is not None else config["models"],
        spans=args.spans if args.spans is not None else config["spans"],
        signs=args.signs if args.signs is not None else config["signs"],
        scope=args.scope,
        embargo_rows=args.embargo_rows if args.embargo_rows is not None else config["embargo_rows"],
    )


if __name__ == "__main__":
    main()
