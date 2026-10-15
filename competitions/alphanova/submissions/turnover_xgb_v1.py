"""Experimental P2/P3 AlphaNova submission candidate, not yet promoted.

A self-contained Predictor with same-hour ranking features and a causal
no-trade band. This file is intentionally independent of research modules.
"""
import numpy as np
import pandas as pd
import xgboost as xgb
from predictor import Predictor


class TurnoverAwareXGBPredictor(Predictor):
    def __init__(self):
        self.model = None
        self.span = 120
        self.min_trade_l1 = 0.01
        self.rebalance_fraction = 1.0
        self.n_rounds = 35
        self.params = {
            "objective": "reg:squarederror",
            "tree_method": "hist",
            "max_depth": 2,
            "eta": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.85,
            "min_child_weight": 500,
            "reg_lambda": 10.0,
            "seed": 42,
            "nthread": 4,
            "verbosity": 0,
        }

    @staticmethod
    def _rank(panel: pd.DataFrame) -> pd.DataFrame:
        ranked = panel.rank(axis=1)
        n = panel.notna().sum(axis=1).to_numpy().reshape(-1, 1)
        return ((ranked - 0.5 * (n + 1)) /
                (0.5 * np.maximum(n - 1, 1))).fillna(0.0)

    def _design(self, features: pd.DataFrame):
        tickers = list(features["Feature.1"].columns)
        raw = [
            features[f"Feature.{i}"].reindex(columns=tickers)
            .replace([np.inf, -np.inf], np.nan)
            for i in range(1, 7)
        ]
        ranked = [self._rank(x) for x in raw]
        blocks = list(ranked)
        blocks.extend([
            self._rank(raw[0] - raw[1]),
            self._rank(raw[2] - raw[3]),
            self._rank(raw[0] - raw[2]),
            self._rank(raw[4] - raw[5]),
            ranked[0] * ranked[1],
            ranked[0] * ranked[2],
            ranked[1] * ranked[3],
            ranked[4] * ranked[5],
        ])
        tensor = np.stack([b.to_numpy(dtype=float) for b in blocks], axis=2)
        design = np.nan_to_num(
            tensor.reshape(-1, tensor.shape[-1]),
            nan=0.0, posinf=0.0, neginf=0.0,
        )
        return design, tickers

    def train(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        X, tickers = self._design(features)
        y = target.reindex(columns=tickers).to_numpy(dtype=float).reshape(-1)
        keep = np.isfinite(y)
        self.model = None
        if keep.any():
            self.model = xgb.train(
                self.params,
                xgb.DMatrix(X[keep], label=y[keep]),
                num_boost_round=self.n_rounds,
            )

    def _apply_policy(self, desired: pd.DataFrame) -> pd.DataFrame:
        values = desired.to_numpy(dtype=float, copy=True)
        values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
        values -= values.mean(axis=1, keepdims=True)
        previous = np.zeros(values.shape[1], dtype=float)
        out = np.empty_like(values)
        for i, target in enumerate(values):
            delta = target - previous
            if np.abs(delta).sum() > self.min_trade_l1:
                previous = previous + self.rebalance_fraction * delta
            out[i] = previous
        out -= out.mean(axis=1, keepdims=True)
        return pd.DataFrame(out, index=desired.index, columns=desired.columns)

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        X, tickers = self._design(features)
        if self.model is None:
            raw = np.zeros((len(features), len(tickers)), dtype=float)
        else:
            raw = self.model.predict(xgb.DMatrix(X)).reshape(len(features), len(tickers))
        desired = pd.DataFrame(raw, columns=tickers, index=features.index)
        desired = desired.ewm(span=self.span, min_periods=1).mean()
        past_mean = desired.shift(1).expanding(min_periods=1).mean()
        desired = (desired - past_mean).fillna(0.0)
        desired = desired.sub(desired.mean(axis=1), axis=0)
        return self._apply_policy(desired).fillna(0.0)
