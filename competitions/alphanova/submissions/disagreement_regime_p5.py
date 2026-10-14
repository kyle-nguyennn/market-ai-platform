"""P5 experimental AlphaNova: rank1 factor conditioned on feature disagreement.

All inference is contemporaneous. Training uses the 20,000-row
pre-embargo history, a training-median regime threshold and half-shrinkage
conditional OLS slopes. Fixed portfolio settings from P4.
"""
import numpy as np
import pandas as pd
from predictor import Predictor


class DisagreementRegimePredictor(Predictor):
    def __init__(self):
        self.train_tail_rows = 20000
        self.embargo_rows = 168
        self.shrinkage = 0.5
        self.span = 240
        self.min_trade_l1 = 0.02
        self.rebalance_fraction = 0.5
        self.threshold = 0.0
        self.beta_global = 0.0
        self.beta_low = 0.0
        self.beta_high = 0.0

    @staticmethod
    def _rank(raw: np.ndarray) -> np.ndarray:
        clean = np.where(np.isfinite(raw), raw, np.nan)
        ranks = pd.DataFrame(clean).rank(axis=1).to_numpy(dtype=float)
        n = np.isfinite(clean).sum(axis=1, keepdims=True)
        scaled = (ranks - 0.5 * (n + 1)) / (
            0.5 * np.maximum(n - 1, 1)
        )
        good = np.isfinite(scaled)
        centered = np.where(good, scaled, 0.0)
        mean = centered.sum(axis=1, keepdims=True) / np.maximum(
            good.sum(axis=1, keepdims=True), 1
        )
        centered = np.where(good, scaled - mean, 0.0)
        return centered - centered.mean(axis=1, keepdims=True)

    def _features(self, features: pd.DataFrame):
        tickers = list(features["Feature.1"].columns)
        x = features["Feature.1"].reindex(columns=tickers).to_numpy(dtype=float)
        y = features["Feature.6"].reindex(columns=tickers).to_numpy(dtype=float)
        rank1 = self._rank(x)
        rank6 = self._rank(y)
        disagreement = np.mean(np.abs(rank1 - rank6), axis=1)
        return rank1, disagreement, tickers

    @staticmethod
    def _slope(factor: np.ndarray, labels: np.ndarray) -> float:
        good = np.isfinite(factor) & np.isfinite(labels)
        x = np.where(good, factor, 0.0)
        y = np.where(good, labels, 0.0)
        denom = np.sum(x * x)
        if denom < 1e-12:
            return 0.0
        return float(np.clip(np.sum(x * y) / denom, -5.0, 5.0))

    def train(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        cutoff = len(features) - self.embargo_rows
        self.beta_global = self.beta_low = self.beta_high = 0.0
        self.threshold = 0.0
        if cutoff <= 0:
            return
        start = max(0, cutoff - self.train_tail_rows)
        train_features = features.iloc[start:cutoff]
        signal, regime, tickers = self._features(train_features)
        labels = target.iloc[start:cutoff].reindex(columns=tickers).to_numpy(dtype=float)
        global_beta = self._slope(signal, labels)
        self.beta_global = global_beta
        finite = regime[np.isfinite(regime)]
        if len(finite) < 2:
            self.beta_low = self.beta_high = global_beta
            return
        self.threshold = float(np.median(finite))
        high = np.isfinite(regime) & (regime > self.threshold)
        low = ~high
        if min(int(high.sum()), int(low.sum())) < 200:
            self.beta_low = self.beta_high = global_beta
            return
        self.beta_low = float(
            (1.0 - self.shrinkage) * global_beta
            + self.shrinkage * self._slope(signal[low], labels[low])
        )
        self.beta_high = float(
            (1.0 - self.shrinkage) * global_beta
            + self.shrinkage * self._slope(signal[high], labels[high])
        )

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        rank1, scores, tickers = self._features(features)
        high = np.isfinite(scores) & (scores > self.threshold)
        slopes = np.where(high, self.beta_high, self.beta_low)
        signal = np.nan_to_num(
            rank1 * slopes[:, None], nan=0.0, posinf=0.0, neginf=0.0
        )
        positions = pd.DataFrame(signal, index=features.index, columns=tickers)
        positions = positions.ewm(span=self.span, min_periods=1).mean()
        historical = positions.shift(1).expanding(min_periods=1).mean()
        desired = (positions - historical).fillna(0.0)
        desired = desired.sub(desired.mean(axis=1), axis=0)
        values = desired.to_numpy(dtype=float, copy=True)
        previous = np.zeros(values.shape[1], dtype=float)
        out = np.empty_like(values)
        for i, target in enumerate(values):
            change = target - previous
            if round(float(np.sort(np.abs(change)).sum()), 12) > self.min_trade_l1:
                previous = previous + self.rebalance_fraction * change
            out[i] = previous
        out -= out.mean(axis=1, keepdims=True)
        return pd.DataFrame(out, columns=tickers, index=features.index)
