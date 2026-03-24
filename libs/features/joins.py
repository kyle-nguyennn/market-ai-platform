"""Point-in-time joins: temporal merge of feature and label DataFrames."""
from __future__ import annotations

import polars as pl


def asof_join(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    on: str,
    by: str | list[str] | None = None,
    strategy: str = "backward",
) -> pl.DataFrame:
    """Perform a point-in-time (as-of) join between *features* and *labels*.

    Uses Polars ``join_asof`` so that each feature row is matched to the
    most recent label row whose ``on`` value is ≤ (or ≥ for strategy="forward")
    the feature's ``on`` value.

    Args:
        features: Left DataFrame (features, sorted by *on*).
        labels: Right DataFrame (labels, sorted by *on*).
        on: Name of the timestamp/sort column.
        by: Optional grouping key(s) (e.g. ticker symbol).
        strategy: ``"backward"`` (default) or ``"forward"``.
    """
    features = features.sort(on)
    labels = labels.sort(on)

    kwargs: dict = {"on": on, "strategy": strategy}
    if by is not None:
        kwargs["by"] = by if isinstance(by, list) else [by]

    return features.join_asof(labels, **kwargs)


def lag_features(
    df: pl.DataFrame,
    feature_cols: list[str],
    lags: list[int],
    sort_col: str = "date",
    group_col: str | None = None,
) -> pl.DataFrame:
    """Add lagged versions of *feature_cols* for each lag in *lags*.

    Column names will be ``{col}_lag{n}``.
    """
    exprs = []
    for col in feature_cols:
        for lag in lags:
            lagged = pl.col(col).shift(lag).alias(f"{col}_lag{lag}")
            exprs.append(lagged)

    if group_col:
        return df.sort(sort_col).with_columns(
            [
                pl.col(col).shift(lag).over(group_col).alias(f"{col}_lag{lag}")
                for col in feature_cols
                for lag in lags
            ]
        )
    return df.sort(sort_col).with_columns(exprs)
