"""Eval Runs page — history and metric trends."""
from __future__ import annotations

import streamlit as st

st.header("Evaluation Runs")
st.info("Connect to eval-control-plane /eval/runs to populate this page.")

st.table(
    [
        {
            "Run ID": "abc-001",
            "Model": "xgb_alpha_v1",
            "Dataset": "daily_equities_v1",
            "ROC-AUC": 0.68,
            "Passed": True,
        }
    ]
)
