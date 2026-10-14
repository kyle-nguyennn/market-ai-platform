"""P4 experimental equal-weight rank1 + diff36 ensemble.

The model combines two independently calibrated contemporaneous signals
before causal smoothing and the frozen P2 turnover policy. Weights are
fixed at 50/50, not searched using the full validation history.
"""
import numpy as np
import pandas as pd
from predictor import Predictor


class FactorBlendPredictor(Predictor):
    def __init__(self):
        self.train_tail_rows = 20000
        self.embargo_rows = 168
        self.span = 240
        self.min_trade_l1 = 0.02
        self.rebalance_fraction = 0.5
        self.beta_rank1 = 0.0
        self.beta_diff36 = 0.0

    @staticmethod
    def _rank(raw: np.ndarray) -> np.ndarray:
        clean = np.where(np.isfinite(raw), raw, np.nan)
        ranks = pd.DataFrame(clean).rank(axis=1).to_numpy(dtype=float)
        n = np.isfinite(clean).sum(axis=1, keepdims=True)
        ranked = (ranks - 0.5 * (n + 1)) / (
            0.5 * np.maximum(n - 1, 1)
        )
        good = np.isfinite(ranked)
        centered = ranked.copy()
        row_mean = np.nansum(centered, axis=1, keepdims=True) / np.maximum(
            good.sum(axis=1, keepdims=True), 1
        )
        centered = np.where(good, centered - row_mean, 0.0)
        return centered - centered.mean(axis=1, keepdims=True)

    def _factors(self, features: pd.DataFrame):
        tickers = list(features["Feature.1"].columns)
        one = features["Feature.1"].reindex(columns=tickers).to_numpy(dtype=float)
        three = features["Feature.3"].reindex(columns=tickers).to_numpy(dtype=float)
        six = features["Feature.6"].reindex(columns=tickers).to_numpy(dtype=float)
        return self._rank(one), self._rank(three - six), tickers

    def _slope(self, values: np.ndarray, target: np.ndarray, end: int) -> float:
        if end <= 0:
            return 0.0
        start = max(0, end - self.train_tail_rows)
        x = values[start:end]
        y = target[start:end]
        valid = np.isfinite(x) & np.isfinite(y)
        xx = np.where(valid, x, 0.0)
        yy = np.where(valid, y, 0.0)
        denom = np.sum(xx * xx)
        if denom < 1e-12:
            return 0.0
        return float(np.clip(np.sum(xx * yy) / denom, -5.0, 5.0))

    def train(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        first, second, tickers = self._factors(features)
        labels = target.reindex(columns=tickers).to_numpy(dtype=float)
        end = len(features) - self.embargo_rows
        self.beta_rank1 = self._slope(first, labels, end)
        self.beta_diff36 = self._slope(second, labels, end)

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        first, second, tickers = self._factors(features)
        signal = 0.5 * (
            self.beta_rank1 * first + self.beta_diff36 * second
        )
        signal = np.nan_to_num(signal, nan=0.0, posinf=0.0, neginf=0.0)
        desired = pd.DataFrame(signal, index=features.index, columns=tickers)
        desired = desired.ewm(span=self.span, min_periods=1).mean()
        historical = desired.shift(1).expanding(min_periods=1).mean()
        desired = (desired - historical).fillna(0.0)
        desired = desired.sub(desired.mean(axis=1), axis=0)
        values = desired.to_numpy(dtype=float, copy=True)
        prior = np.zeros(values.shape[1], dtype=float)
        output = np.empty_like(values)
        for i, goal in enumerate(values):
            delta = goal - prior
            if np.abs(delta).sum() > self.min_trade_l1:
                prior = prior + self.rebalance_fraction * delta
            output[i] = prior
        output -= output.mean(axis=1, keepdims=True)
        return pd.DataFrame(output, index=features.index, columns=tickers)
