"""Datasets page — catalog and quality scores."""
from __future__ import annotations

import streamlit as st

st.header("Dataset Catalog")
st.info("Connect to dataset-platform /datasets to populate this page.")

st.table(
    [
        {
            "Name": "daily_equities_v1",
            "Version": "1.0.0",
            "Status": "ready",
            "Rows": "~250k",
            "Quality": "pass",
        }
    ]
)
