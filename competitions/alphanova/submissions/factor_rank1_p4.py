"""P4 AlphaNova standalone Feature1RankPredictor candidate; experimental only.

The factor hypothesis was selected on discovery periods. Uses 168-row
training-label embargo, last 20,000 earlier samples, and the P2 fixed
causal position construction. This model must pass full official
walk-forward validation before being considered for submission.
"""
import numpy as np
import pandas as pd
from predictor import Predictor


class Feature1RankPredictor(Predictor):
    def __init__(self):
        self.train_tail_rows = 20000
        self.embargo_rows = 168
        self.span = 240
        self.min_trade_l1 = 0.02
        self.rebalance_fraction = 0.5
        self.beta = 0.0

    @staticmethod
    def _rank(raw: np.ndarray) -> np.ndarray:
        clean = np.where(np.isfinite(raw), raw, np.nan)
        ranks = pd.DataFrame(clean).rank(axis=1).to_numpy(dtype=float)
        n = np.isfinite(clean).sum(axis=1, keepdims=True)
        values = (ranks - 0.5 * (n + 1)) / (0.5 * np.maximum(n - 1, 1))
        values = np.where(np.isfinite(values), values, np.nan)
        count = np.sum(np.isfinite(values), axis=1, keepdims=True)
        mean = np.nansum(values, axis=1, keepdims=True) / np.maximum(count, 1)
        values = np.where(np.isfinite(values), values - mean, 0.0)
        return values - values.mean(axis=1, keepdims=True)

    def _factor(self, features: pd.DataFrame):
        tickers = list(features["Feature.1"].columns)
        x = features["Feature.1"].reindex(columns=tickers).to_numpy(dtype=float)
        signal = self._rank(x)
        return signal, tickers

    def train(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        signal, tickers = self._factor(features)
        labels = target.reindex(columns=tickers).to_numpy(dtype=float)
        end = len(features) - self.embargo_rows
        self.beta = 0.0
        if end <= 0:
            return
        start = max(0, end - self.train_tail_rows)
        x = signal[start:end]
        y = labels[start:end]
        valid = np.isfinite(x) & np.isfinite(y)
        xx = np.where(valid, x, 0.0)
        yy = np.where(valid, y, 0.0)
        denom = np.sum(xx * xx)
        if denom > 1e-12:
            self.beta = float(np.clip(np.sum(xx * yy) / denom, -5.0, 5.0))

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        factor, tickers = self._factor(features)
        values = np.nan_to_num(
            self.beta * factor, nan=0.0, posinf=0.0, neginf=0.0
        )
        positions = pd.DataFrame(values, index=features.index, columns=tickers)
        positions = positions.ewm(span=self.span, min_periods=1).mean()
        past_mean = positions.shift(1).expanding(min_periods=1).mean()
        desired = (positions - past_mean).fillna(0.0)
        desired = desired.sub(desired.mean(axis=1), axis=0)
        values = desired.to_numpy(dtype=float, copy=True)
        prior = np.zeros(values.shape[1], dtype=float)
        out = np.empty_like(values)
        for i, goal in enumerate(values):
            delta = goal - prior
            if np.abs(delta).sum() > self.min_trade_l1:
                prior = prior + self.rebalance_fraction * delta
            out[i] = prior
        out -= out.mean(axis=1, keepdims=True)
        return pd.DataFrame(out, index=features.index, columns=tickers)
