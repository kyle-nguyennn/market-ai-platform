"""AlphaNova P1: low-capacity Ridge baseline using contemporaneous rankings.

Submit this file as a single artifact; no imports from the research package.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from predictor import Predictor


class RidgeCrossSectionalPredictor(Predictor):
    def __init__(self):
        self.alpha = 1000.0
        self.span = 120
        self.model = None

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
        blocks = [self._rank(x) for x in raw]
        blocks += [
            self._rank(raw[0] - raw[1]),
            self._rank(raw[2] - raw[3]),
            self._rank(raw[0] - raw[2]),
            self._rank(raw[4] - raw[5]),
        ]
        tensor = np.stack([b.to_numpy(dtype=float) for b in blocks], axis=2)
        design = tensor.reshape(-1, tensor.shape[-1])
        return np.nan_to_num(design, nan=0.0, posinf=0.0, neginf=0.0), tickers

    def train(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        X, tickers = self._design(features)
        y = target.reindex(columns=tickers).to_numpy(dtype=float).reshape(-1)
        valid = np.isfinite(y)
        if not valid.any():
            self.model = None
            return
        self.model = Ridge(alpha=self.alpha, solver="lsqr")
        self.model.fit(X[valid], y[valid])

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        X, tickers = self._design(features)
        if self.model is None:
            raw = np.zeros((len(features), len(tickers)), dtype=float)
        else:
            raw = self.model.predict(X).reshape(len(features), len(tickers))
        positions = pd.DataFrame(raw, columns=tickers, index=features.index)
        positions = positions.ewm(span=self.span, min_periods=1).mean()
        historical_tilt = positions.shift(1).expanding(min_periods=1).mean()
        positions = (positions - historical_tilt).fillna(0.0)
        positions = positions.sub(positions.mean(axis=1), axis=0)
        return positions.fillna(0.0)
