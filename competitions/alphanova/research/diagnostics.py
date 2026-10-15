"""Pure PnL and validation diagnostics for AlphaNova research.

Replicates evaluation.backtest's lag and 5bp cost convention. No model fitting,
dataset access, or competition modifications happen here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRANSACTION_COST = 0.0005


def sharpe(returns: pd.Series) -> float:
    """Unannualized mean/sample-std Sharpe (official local convention)."""
    if len(returns) < 2:
        return 0.0
    std = float(returns.std())
    return float(returns.mean() / std) if np.isfinite(std) and std > 0 else 0.0


def pnl_components(
    predictions: pd.DataFrame,
    returns: pd.DataFrame,
    cost_rate: float = TRANSACTION_COST,
) -> pd.DataFrame:
    """Compute lagged gross PnL, L1 turnover and net PnL in row order.

    The first row is flat, as in the supplied evaluation.backtest().
    Column labels, not their original physical order, align positions to returns.
    """
    if len(predictions) != len(returns):
        raise ValueError("Prediction and return row counts differ")
    if set(predictions.columns) != set(returns.columns):
        raise ValueError("Prediction and return ticker columns differ")
    if not np.isfinite(predictions.to_numpy(dtype=float)).all():
        raise ValueError("Predictions contain non-finite positions")

    p = predictions.reindex(columns=returns.columns).copy()
    p.index = returns.index
    p = p.ffill()
    held = p.shift(1)
    gross = (held * returns).sum(axis=1)
    turnover = held.fillna(0.0).diff().abs().sum(axis=1)
    cost = cost_rate * turnover
    net = gross - cost
    if len(net):
        gross.iloc[0] = 0.0
        turnover.iloc[0] = 0.0
        cost.iloc[0] = 0.0
        net.iloc[0] = 0.0
    return pd.DataFrame(
        {"gross": gross, "turnover": turnover, "cost": cost, "net": net},
        index=returns.index,
    )


def summarize(pnl: pd.DataFrame) -> dict[str, float | int]:
    """Diagnostics for one period or concatenated out-of-sample observations."""
    n = len(pnl)
    return {
        "observations": n,
        "gross_sharpe": sharpe(pnl["gross"]),
        "net_sharpe": sharpe(pnl["net"]),
        "mean_gross": float(pnl["gross"].mean()) if n else 0.0,
        "mean_net": float(pnl["net"].mean()) if n else 0.0,
        "mean_turnover": float(pnl["turnover"].mean()) if n else 0.0,
        "mean_cost": float(pnl["cost"].mean()) if n else 0.0,
        "total_net_pnl": float(pnl["net"].sum()),
        "positive_fraction": float((pnl["net"] > 0).mean()) if n else 0.0,
    }


def new_history_slice(
    validation_pnl: pd.DataFrame,
    train_rows: int,
    previous_period_rows: int | None,
) -> pd.DataFrame:
    """Keep only newly introduced cumulative-history rows for each period.

    Period files are cumulative. Under the kit's cumulative row-position
    contract, a row with original position < previous_period_rows is repeated
    history. If the newest period adds more than the validation size, this
    subset is not exhaustive; the official 800-row holdout limits coverage.
    """
    if previous_period_rows is None:
        return validation_pnl
    if previous_period_rows < 0:
        raise ValueError("Invalid previous-period size")
    first_new_in_validation = max(0, previous_period_rows - train_rows)
    return validation_pnl.iloc[first_new_in_validation:]


def assert_valid_predictions(predictions: pd.DataFrame, returns: pd.DataFrame) -> None:
    if len(predictions) != len(returns):
        raise ValueError("Prediction row count differs from validation returns")
    if set(predictions.columns) != set(returns.columns):
        raise ValueError("Ticker mismatch")
    array = predictions.to_numpy(dtype=float)
    if not np.isfinite(array).all():
        raise ValueError("Non-finite predictions")
    if array.shape[1] == 0 or not np.allclose(array.mean(axis=1), 0.0, atol=1e-6):
        raise ValueError("NOT_DEMEANED")
