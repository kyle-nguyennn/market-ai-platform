"""Classification and ranking metrics for model evaluation."""
from __future__ import annotations

import numpy as np


def accuracy(y_true: list[int], y_pred: list[int]) -> float:
    arr_true = np.array(y_true)
    arr_pred = np.array(y_pred)
    return float((arr_true == arr_pred).mean())


def precision_recall_f1(
    y_true: list[int],
    y_pred: list[int],
) -> tuple[float, float, float]:
    """Return (precision, recall, f1) for the positive class (label=1)."""
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return precision, recall, f1


def roc_auc(y_true: list[int], y_score: list[float]) -> float:
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y_true, y_score))


def log_loss(y_true: list[int], y_score: list[float]) -> float:
    from sklearn.metrics import log_loss as _log_loss
    return float(_log_loss(y_true, y_score))


def information_coefficient(y_true: list[float], y_pred: list[float]) -> float:
    """Rank IC (Spearman) between predicted scores and realised returns."""
    from scipy.stats import spearmanr
    corr, _ = spearmanr(y_true, y_pred)
    return float(corr)
