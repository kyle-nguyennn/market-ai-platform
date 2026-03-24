"""Streamlit ops dashboard entry point."""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Market AI Platform — Ops Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("Market AI Platform — Ops Dashboard")

st.markdown(
    """
    Use the sidebar to navigate between sections:

    - **Models** — live model deployments, stage status, canary traffic weights
    - **Datasets** — dataset catalog, quality scores, build history
    - **Eval Runs** — evaluation history, metric trends, regression guards
    - **Drift** — feature and score drift alerts, PSI / KS heatmaps
    """
)

# Each page is implemented in ui/ops-dashboard/pages/
