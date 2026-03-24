"""Reusable Streamlit table helpers for the ops dashboard."""
from __future__ import annotations

import polars as pl


def model_status_table(models: list[dict]) -> None:
    """Render a Streamlit table showing model name, version, stage, and metrics."""
    import streamlit as st

    df = pl.DataFrame(models)
    st.dataframe(df.to_pandas(), use_container_width=True)


def eval_history_table(runs: list[dict]) -> None:
    """Render evaluation run history with pass/fail colouring."""
    import streamlit as st

    if not runs:
        st.info("No evaluation runs found.")
        return

    df = pl.DataFrame(runs)
    st.dataframe(
        df.to_pandas().style.apply(
            lambda row: [
                "background-color: #ccffcc" if row.get("passed") else "background-color: #ffcccc"
            ] * len(row),
            axis=1,
        ),
        use_container_width=True,
    )


def dataset_catalog_table(datasets: list[dict]) -> None:
    """Render the dataset catalog with status badges."""
    import streamlit as st

    if not datasets:
        st.info("No datasets registered.")
        return
    df = pl.DataFrame(datasets)
    st.dataframe(df.to_pandas(), use_container_width=True)
