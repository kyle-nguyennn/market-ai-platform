"""Models page — live deployment status."""
from __future__ import annotations

import streamlit as st

st.header("Model Deployments")
st.info("Connect to inference-gateway /models to populate this page.")

# Placeholder table
st.table(
    [
        {"Name": "xgb_alpha_v1", "Version": "1.0.0", "Stage": "production", "Traffic": "100%"},
        {"Name": "xgb_alpha_v2", "Version": "2.0.0", "Stage": "canary", "Traffic": "10%"},
    ]
)
