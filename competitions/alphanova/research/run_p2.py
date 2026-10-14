"""AlphaNova P2: turnover policy grid using cached model fits per period.

Use --scope full for the 31-period research run. Never treat best in-sample
grid results as an untouched test set; the runner's periods are reusable.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

from competitions.alphanova.research.diagnostics import (
    assert_valid_predictions,
    new_history_slice,
    pnl_components,
    summarize,
)
from competitions.alphanova.research.positions import (
    policy_diagnostics,
    position_policy,
)
from competitions.alphanova.research.run_experiments import KIT, REGISTRY

from data_loader import list_periods, load_period
from walkforward import compute_val_rows


def run(
    data_dir: Path,
    output_dir: Path,
    models: list[str],
    spans: list[int],
    trade_bands: list[float],
    rebalance_fractions: list[float],
    scope: str,
    period_keys: list[str] | None = None,
) -> list[dict]:
    periods = list_periods(str(data_dir))
    if period_keys is not None:
        missing = set(period_keys) - set(periods)
        if missing:
            raise ValueError(f"Unknown periods: {sorted(missing)}")
        periods = [p for p in periods if p in set(period_keys)]
    if scope == "latest":
        periods = periods[-1:]
    if not periods:
        raise ValueError("No training periods found; verify LFS checkout")
    if any(m not in REGISTRY for m in models):
        raise ValueError("Unknown model")
    if any(s < 1 for s in spans):
        raise ValueError("Invalid EWM span")

    grouped = defaultdict(list)
    grouped_new = defaultdict(list)
    per_period: list[dict] = []
    previous_rows = None

    for period in periods:
        frame = load_period(period, str(data_dir))
        features, targets, returns = (
            frame["features"], frame["target"], frame["returns"]
        )
        n = len(features)
        cut = n - compute_val_rows(n)
        train_features, train_targets = features.iloc[:cut], targets.iloc[:cut]
        val_features, val_returns = features.iloc[cut:], returns.iloc[cut:]
        print(f"[P2 {period}] train={cut} validation={len(val_features)}", flush=True)

        for name in models:
            predictor = REGISTRY[name]()
            if hasattr(predictor, "generate_features"):
                predictor.generate_features(features)
            start = time.monotonic()
            predictor.train(train_features, train_targets)
            train_sec = time.monotonic() - start
            if train_sec > 240:
                raise TimeoutError(f"Training too slow: {name} {train_sec:.1f}s")
            for span in spans:
                predictor.span = span
                start = time.monotonic()
                raw = predictor.predict(val_features)
                predict_sec = time.monotonic() - start
                if predict_sec > 60:
                    raise TimeoutError(f"Prediction too slow: {name} {predict_sec:.1f}s")
                assert_valid_predictions(raw, val_returns)

                for band in trade_bands:
                    for fraction in rebalance_fractions:
                        start = time.monotonic()
                        predictions = position_policy(raw, band, fraction)
                        policy_sec = time.monotonic() - start
                        if predict_sec + policy_sec > 60:
                            raise TimeoutError("Inference + portfolio control too slow")
                        assert_valid_predictions(predictions, val_returns)
                        pnl = pnl_components(predictions, val_returns)
                        novel = new_history_slice(pnl, cut, previous_rows)
                        key = (name, span, band, fraction)
                        grouped[key].append(pnl)
                        grouped_new[key].append(novel)
                        item = {
                            "period": period,
                            "model": name,
                            "span": span,
                            "trade_band": band,
                            "rebalance_fraction": fraction,
                            "train_seconds": train_sec,
                            "predict_seconds": predict_sec + policy_sec,
                        }
                        item.update(summarize(pnl))
                        item.update(policy_diagnostics(predictions))
                        per_period.append(item)
        previous_rows = n

    summary = []
    for key, pnl_frames in grouped.items():
        name, span, band, fraction = key
        rows = [r for r in per_period if
                (r["model"], r["span"], r["trade_band"],
                 r["rebalance_fraction"]) == key]
        aggregate = pd.concat(pnl_frames, ignore_index=True)
        independent = pd.concat(grouped_new[key], ignore_index=True)
        record = {
            "model": name,
            "span": span,
            "trade_band": band,
            "rebalance_fraction": fraction,
            "periods": len(periods),
            "positive_periods": sum(r["net_sharpe"] > 0 for r in rows),
            "max_train_seconds": max(r["train_seconds"] for r in rows),
            "max_predict_seconds": max(r["predict_seconds"] for r in rows),
            "mean_rebalance_fraction_observed": sum(
                r["rebalance_fraction_observed"] for r in rows
            ) / len(rows),
        }
        record.update(summarize(aggregate))
        record.update({
            "new_history_" + k: v for k, v in summarize(independent).items()
        })
        summary.append(record)

    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(per_period).to_csv(output_dir / "per_period.csv", index=False)
    pd.DataFrame(summary).sort_values(
        "net_sharpe", ascending=False
    ).to_csv(output_dir / "summary.csv", index=False)
    manifest = {
        "scope": scope,
        "periods": periods,
        "models": models,
        "spans": spans,
        "trade_bands": trade_bands,
        "rebalance_fractions": rebalance_fractions,
        "position_reset": "Every validation frame starts flat",
        "warning": (
            "Exploratory multiple-comparison results; full history reused "
            "for selection, not an untouched holdout."
        ),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("\nP2 top net-Sharpe configurations", flush=True)
    for r in sorted(summary, key=lambda x: x["net_sharpe"], reverse=True)[:12]:
        print(
            f"{r['model']:17} span={r['span']:3d} "
            f"band={r['trade_band']:.3f} fraction={r['rebalance_fraction']:.2f} "
            f"gross={r['gross_sharpe']:+.5f} net={r['net_sharpe']:+.5f} "
            f"nonoverlap={r['new_history_net_sharpe']:+.5f}",
            flush=True,
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("latest", "full"), default="latest")
    parser.add_argument("--period-keys", nargs="+", default=None)
    parser.add_argument("--config", type=Path, default=(
        Path(__file__).resolve().parents[1] / "configs/p2_grid.json"
    ))
    parser.add_argument("--output-dir", type=Path, default=(
        Path(__file__).resolve().parents[1] / "results/p2"
    ))
    parser.add_argument("--data-dir", type=Path, default=KIT / "data/train")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    run(args.data_dir, args.output_dir, config["models"], config["spans"],
        config["trade_bands"], config["rebalance_fractions"],
        args.scope, args.period_keys)


if __name__ == "__main__":
    main()
