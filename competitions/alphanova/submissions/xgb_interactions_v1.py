"""AlphaNova P1: regularized XGBoost on same-hour cross-sectional interactions."""
import numpy as np
import pandas as pd
import xgboost as xgb
from predictor import Predictor


class XGBInteractionPredictor(Predictor):
    def __init__(self):
        self.span = 120
        self.n_rounds = 35
        self.model = None
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
        r = panel.rank(axis=1)
        n = panel.notna().sum(axis=1).to_numpy().reshape(-1, 1)
        return ((r - 0.5 * (n + 1)) / (0.5 * np.maximum(n - 1, 1))).fillna(0.0)

    def _design(self, features: pd.DataFrame):
        tickers = list(features["Feature.1"].columns)
        raw = [
            features[f"Feature.{i}"].reindex(columns=tickers)
            for i in range(1, 7)
        ]
        ranks = [self._rank(x) for x in raw]
        blocks = list(ranks)
        blocks.extend([
            self._rank(raw[0] - raw[1]),
            self._rank(raw[2] - raw[3]),
            self._rank(raw[0] - raw[2]),
            self._rank(raw[4] - raw[5]),
            ranks[0] * ranks[1],
            ranks[0] * ranks[2],
            ranks[1] * ranks[3],
            ranks[4] * ranks[5],
        ])
        tensor = np.stack([b.to_numpy(dtype=float) for b in blocks], axis=2)
        X = tensor.reshape(-1, tensor.shape[-1])
        return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0), tickers

    def train(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        X, tickers = self._design(features)
        y = target.reindex(columns=tickers).to_numpy(dtype=float).reshape(-1)
        valid = np.isfinite(y)
        if not valid.any():
            self.model = None
            return
        self.model = xgb.train(
            self.params, xgb.DMatrix(X[valid], label=y[valid]),
            num_boost_round=self.n_rounds,
        )

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        X, tickers = self._design(features)
        if self.model is None:
            raw = np.zeros((len(features), len(tickers)), dtype=float)
        else:
            raw = self.model.predict(xgb.DMatrix(X)).reshape(len(features), len(tickers))
        positions = pd.DataFrame(raw, columns=tickers, index=features.index)
        positions = positions.ewm(span=self.span, min_periods=1).mean()
        historical_tilt = positions.shift(1).expanding(min_periods=1).mean()
        positions = (positions - historical_tilt).fillna(0.0)
        positions = positions.sub(positions.mean(axis=1), axis=0)
        return positions.fillna(0.0)
