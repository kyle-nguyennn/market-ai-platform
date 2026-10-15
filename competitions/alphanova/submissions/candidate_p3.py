"""Experimental AlphaNova P3: turnover-optimized engineered XGBoost.

Self-contained single-file Predictor. Default controls mirror the best P2
walk-forward configuration; not evidence of a positive-alpha strategy.
"""
import numpy as np
import pandas as pd
import xgboost as xgb
from predictor import Predictor


class EngineeredTurnoverPredictor(Predictor):
    def __init__(self):
        self.model = None
        self.span = 240
        self.min_trade_l1 = 0.02
        self.rebalance_fraction = 0.5
        self.n_rounds = 30
        self.params = {
            "objective": "reg:squarederror",
            "max_depth": 2,
            "eta": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 500,
            "reg_lambda": 5.0,
            "verbosity": 0,
            "nthread": 4,
        }

    @staticmethod
    def _rank(frame: pd.DataFrame) -> pd.DataFrame:
        rank = frame.rank(axis=1)
        n = frame.notna().sum(axis=1).to_numpy().reshape(-1, 1)
        return (rank - 0.5 * (n + 1)) / (0.5 * np.maximum(n - 1, 1))

    def _design(self, features: pd.DataFrame):
        g = {i: features[f"Feature.{i}"] for i in range(1, 7)}
        blocks = {
            "a": self._rank(g[6]),
            "m": self._rank(g[1]),
            "p": self._rank(g[1] - g[2]),
            "q": self._rank(g[3] - g[4]),
            "r": self._rank(g[1] - g[3]),
            "s": self._rank(g[5]),
        }
        tickers = list(blocks["a"].columns)
        X = np.hstack([
            block[tickers].to_numpy(dtype=float).reshape(-1, 1)
            for block in blocks.values()
        ])
        return X, tickers

    def train(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        X, tickers = self._design(features)
        y = target.reindex(columns=tickers).to_numpy(dtype=float).reshape(-1)
        good = np.isfinite(y) & np.isfinite(X).all(axis=1)
        self.model = None
        if good.any():
            self.model = xgb.train(
                self.params, xgb.DMatrix(X[good], label=y[good]),
                num_boost_round=self.n_rounds,
            )

    def _rebalance(self, desired: pd.DataFrame) -> pd.DataFrame:
        matrix = np.nan_to_num(desired.to_numpy(dtype=float, copy=True),
                               nan=0.0, posinf=0.0, neginf=0.0)
        matrix -= matrix.mean(axis=1, keepdims=True)
        last = np.zeros(matrix.shape[1], dtype=float)
        result = np.empty_like(matrix)
        for row, goal in enumerate(matrix):
            delta = goal - last
            if np.abs(delta).sum() > self.min_trade_l1:
                last = last + self.rebalance_fraction * delta
            result[row] = last
        result -= result.mean(axis=1, keepdims=True)
        return pd.DataFrame(result, index=desired.index, columns=desired.columns)

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        X, tickers = self._design(features)
        if self.model is None:
            flat = np.zeros((len(features), len(tickers)), dtype=float)
            positions = pd.DataFrame(flat, index=features.index, columns=tickers)
            return self._rebalance(positions)
        raw = self.model.predict(xgb.DMatrix(np.nan_to_num(X)))
        positions = pd.DataFrame(
            raw.reshape(-1, len(tickers)), index=features.index, columns=tickers
        )
        positions = positions.ewm(span=self.span, min_periods=1).mean()
        tilt = positions.shift(1).expanding(min_periods=1).mean()
        positions = (positions - tilt).fillna(0.0)
        positions = positions.sub(positions.mean(axis=1), axis=0)
        return self._rebalance(positions).fillna(0.0)
