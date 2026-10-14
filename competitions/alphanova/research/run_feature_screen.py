"""P4 cross-sectional feature discovery on fixed historical validation periods.

Selection is made strictly on discovery periods before *any* confirmation
periods are loaded. A confirmation set is not an untouched final test if
other previous research already used those periods.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from competitions.alphanova.research.diagnostics import (
    assert_valid_predictions,
    pnl_components,
    summarize,
)
from competitions.alphanova.research.feature_screen import (
    cross_rank,
    cross_sectional_ic,
    factor_names,
    factor_values,
    feature_panels,
    train_linear_slope,
)
from competitions.alphanova.research.positions import position_policy

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "external" / "alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))

from data_loader import load_period  # noqa: E402


def mean_finite(values: np.ndarray) -> float:
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    return float(v.mean()) if len(v) else 0.0


def validation_prediction(
    panel: np.ndarray,
    beta: float,
    index: pd.Index,
    tickers: list[str],
    span: int,
    trade_band: float,
    rebalance_fraction: float,
) -> pd.DataFrame:
    """Factor beta learned earlier; causal signal smoothing and turnover policy."""
    raw = np.nan_to_num(beta * panel, nan=0.0, posinf=0.0, neginf=0.0)
    positions = pd.DataFrame(raw, index=index, columns=tickers)
    positions = positions.ewm(span=span, min_periods=1).mean()
    tilt = positions.shift(1).expanding(min_periods=1).mean()
    desired = (positions - tilt).fillna(0.0)
    desired = desired.sub(desired.mean(axis=1), axis=0)
    return position_policy(desired, trade_band, rebalance_fraction)


def analyze_period(
    period: str,
    names: list[str],
    data_dir: Path,
    config: dict,
    phase: str,
) -> list[dict]:
    panels = load_period(period, str(data_dir))
    features, labels, returns = (
        panels["features"], panels["target"], panels["returns"]
    )
    n = len(features)
    n_val = min(800, int(0.2 * n))
    n_train = n - n_val
    embargo = int(config["embargo_rows"])
    train_end = n_train - embargo
    if train_end < 100:
        raise ValueError(f"Insufficient pre-validation data in period {period}")

    raw, tickers = feature_panels(features)
    ranked = [cross_rank(arr) for arr in raw]
    y = labels.reindex(columns=tickers).to_numpy(dtype=float)
    val_y = y[n_train:]
    val_returns = returns.iloc[n_train:].reindex(columns=tickers)
    val_index = val_returns.index
    span = int(config["span"])
    band = float(config["trade_band"])
    rebalance = float(config["rebalance_fraction"])
    rows = []

    for name in names:
        full = factor_values(name, raw, ranked)
        if full.shape != y.shape:
            raise ValueError(f"{name}: factor dimension mismatch")
        beta = train_linear_slope(
            full, y, train_end, int(config["train_tail_rows"])
        )
        val = full[n_train:]
        signed_ic = cross_sectional_ic(
            np.sign(beta) * val, val_y
        )
        raw_ic = cross_sectional_ic(val, val_y)
        positions = validation_prediction(
            val, beta, val_index, tickers, span, band, rebalance
        )
        assert_valid_predictions(positions, val_returns)
        pnl = pnl_components(positions, val_returns)
        scores = summarize(pnl)
        row = {
            "phase": phase,
            "period": period,
            "name": name,
            "family": name.split("_")[0],
            "train_rows": train_end,
            "val_rows": n_val,
            "train_slope": beta,
            "raw_target_ic": mean_finite(raw_ic),
            "signed_target_ic": mean_finite(signed_ic),
            "valid_target_ic_rows": int(np.isfinite(signed_ic).sum()),
        }
        row.update(scores)
        rows.append(row)
    print(
        f"[{phase} {period}] evaluated={len(rows)} "
        f"train={train_end} val={n_val}",
        flush=True,
    )
    return rows


def summarize_factors(rows: list[dict]) -> pd.DataFrame:
    """Concatenated PnL moments from period summaries (equal 800 rows each).

    Within-period PnL is not retained to keep 48-factor screening cheap.
    Sample std is reconstructed exactly from period mean and sample std,
    not approximated by averaging each period's Sharpe.
    """
    grouped = []
    for name, group in pd.DataFrame(rows).groupby("name", sort=False):
        record = {
            "name": name,
            "family": group.iloc[0]["family"],
            "periods": len(group),
            "observations": int(group["observations"].sum()),
            "positive_periods": int((group["net_sharpe"] > 0).sum()),
            "positive_gross_periods": int((group["gross_sharpe"] > 0).sum()),
            "signed_target_ic": float(
                np.average(group["signed_target_ic"], weights=group["val_rows"])
            ),
            "mean_abs_train_slope": float(group["train_slope"].abs().mean()),
            "positive_beta_periods": int((group["train_slope"] > 0).sum()),
            "mean_turnover": float(
                np.average(group["mean_turnover"], weights=group["observations"])
            ),
            "mean_cost": float(
                np.average(group["mean_cost"], weights=group["observations"])
            ),
        }
        n = record["observations"]
        for col in ("net", "gross"):
            means = group[f"mean_{col}"].to_numpy(dtype=float)
            count = group["observations"].to_numpy(dtype=int)
            # Derive sample standard deviations from period Sharpe and mean.
            sharpes = group[f"{col}_sharpe"].to_numpy(dtype=float)
            stds = np.divide(
                means, sharpes, out=np.zeros_like(means),
                where=np.abs(sharpes) > 1e-12,
            )
            # When Sharpe=0 due to near-zero sample mean, this can lose
            # variance information. Aggregate moments are a research
            # approximation; the per-period statistics remain authoritative.
            total_mean = float(np.dot(count, means) / n)
            total_ss = float(
                np.sum((count - 1) * stds * stds + count * (means - total_mean) ** 2)
            )
            std = np.sqrt(max(0.0, total_ss) / max(n - 1, 1))
            record[f"{col}_sharpe"] = total_mean / std if std > 0 else 0.0
            record[f"mean_{col}"] = total_mean
        grouped.append(record)
    return pd.DataFrame(grouped).sort_values(
        ["net_sharpe", "signed_target_ic"], ascending=False
    ).reset_index(drop=True)


def validate_config(config: dict) -> None:
    discovery = config["discovery_periods"]
    confirmation = config["confirmation_periods"]
    if not discovery or not confirmation:
        raise ValueError("Both chronological discovery and confirmation periods required")
    if any(x >= y for x in discovery for y in confirmation):
        raise ValueError("Discovery periods must be earlier than confirmation periods")
    if sorted(discovery) != discovery or sorted(confirmation) != confirmation:
        raise ValueError("Periods must be sorted")
    if len(discovery) != len(set(discovery)) or len(confirmation) != len(set(confirmation)):
        raise ValueError("Duplicate period keys")
    if not 0 < config["top_k"] <= len(factor_names()):
        raise ValueError("Invalid top_k")


def run(config: dict, data_dir: Path, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    validate_config(config)
    catalog = factor_names()
    # Crucially do not load *any* confirmation data before freezing the
    # top-k names from the entire exploratory discovery set.
    discovery_rows: list[dict] = []
    for period in config["discovery_periods"]:
        discovery_rows.extend(
            analyze_period(period, catalog, data_dir, config, "discovery")
        )
    discovery = summarize_factors(discovery_rows)
    selected = discovery.head(int(config["top_k"]))["name"].tolist()
    print("\nFrozen factor shortlist (discovery only):", selected, flush=True)

    confirmation_rows: list[dict] = []
    for period in config["confirmation_periods"]:
        confirmation_rows.extend(
            analyze_period(period, selected, data_dir, config, "confirmation")
        )
    confirmation = summarize_factors(confirmation_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(discovery_rows).to_csv(
        output_dir / "discovery_per_period.csv", index=False
    )
    discovery.to_csv(output_dir / "discovery_summary.csv", index=False)
    pd.DataFrame(confirmation_rows).to_csv(
        output_dir / "confirmation_per_period.csv", index=False
    )
    confirmation.to_csv(output_dir / "confirmation_summary.csv", index=False)
    manifest = {
        **config,
        "catalog": catalog,
        "frozen_selected": selected,
        "selection_metric": "discovery net_sharpe",
        "caveat": (
            "Exploratory time-period validation; confirmation periods have "
            "already appeared in earlier P0-P3 model research. Results are "
            "not untouched hidden/live test performance. Aggregate Sharpe "
            "is moment-reconstructed from per-period summaries."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print("\nTOP DISCOVERY:", flush=True)
    print(discovery.head(10)[
        ["name", "net_sharpe", "gross_sharpe",
         "signed_target_ic", "positive_periods"]
    ].to_string(index=False), flush=True)
    print("\nPRESELECTED FACTORS — CONFIRMATION:", flush=True)
    print(confirmation[
        ["name", "net_sharpe", "gross_sharpe",
         "signed_target_ic", "positive_periods"]
    ].to_string(index=False), flush=True)
    return discovery, confirmation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "competitions/alphanova/configs/p4_factors.json"
    )
    parser.add_argument("--data-dir", type=Path, default=KIT / "data/train")
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "competitions/alphanova/results/p4"
    )
    args = parser.parse_args()
    run(json.loads(args.config.read_text()), args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()
