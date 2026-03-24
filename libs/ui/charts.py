"""Reusable Streamlit chart components for the ops dashboard."""
from __future__ import annotations

from typing import Any

import polars as pl


def line_chart(df: pl.DataFrame, x: str, y: str | list[str], title: str = "") -> None:
    """Render a Streamlit line chart from a Polars DataFrame.

    Args:
        df: Source data.
        x: Column to use as the x-axis.
        y: One or more column names to plot on the y-axis.
        title: Optional chart title rendered above the chart.
    """
    import streamlit as st

    if title:
        st.subheader(title)
    y_cols = [y] if isinstance(y, str) else y
    pandas_df = df.select([x, *y_cols]).to_pandas().set_index(x)
    st.line_chart(pandas_df)


def bar_chart(df: pl.DataFrame, x: str, y: str, title: str = "") -> None:
    """Render a Streamlit bar chart."""
    import streamlit as st

    if title:
        st.subheader(title)
    pandas_df = df.select([x, y]).to_pandas().set_index(x)
    st.bar_chart(pandas_df)


def metric_row(metrics: dict[str, Any]) -> None:
    """Display a horizontal row of Streamlit metric widgets.

    Args:
        metrics: Mapping of label → value (or (value, delta) tuple).
    """
    import streamlit as st

    cols = st.columns(len(metrics))
    for col, (label, val) in zip(cols, metrics.items()):
        if isinstance(val, tuple):
            col.metric(label, val[0], delta=val[1])
        else:
            col.metric(label, val)


def drift_heatmap(drift_data: dict[str, dict[str, float]], title: str = "Feature Drift") -> None:
    """Display PSI values for each feature as a colour-coded table."""
    import streamlit as st

    rows = [
        {"Feature": feat, "PSI": info.get("psi"),
         "KS": info.get("ks_statistic"), "Passed": info.get("passed")}
        for feat, info in drift_data.items()
    ]
    drift_df = pl.DataFrame(rows)
    st.subheader(title)
    st.dataframe(
        drift_df.to_pandas().style.applymap(
            lambda v: "background-color: #ffcccc" if v is False else "",
            subset=["Passed"],
        )
    )
