"""Drift monitoring page — PSI / KS heatmaps and alerts."""
from __future__ import annotations

import streamlit as st

st.header("Feature & Score Drift")
st.info("Connect to eval-control-plane /eval/drift/alerts to populate this page.")

st.subheader("Recent Drift Alerts")
st.table(
    [
        {
            "Feature": "vol_20d",
            "PSI": 0.23,
            "KS": 0.11,
            "Threshold Exceeded": "PSI",
            "Model": "xgb_alpha_v1",
        }
    ]
)
