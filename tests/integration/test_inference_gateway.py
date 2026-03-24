"""Integration tests for inference-gateway service."""
from __future__ import annotations

from fastapi.testclient import TestClient

from services.inference_gateway.app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "inference-gateway"


def test_list_models_empty():
    resp = client.get("/models/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_score_returns_503_without_model():
    payload = {
        "model_name": "xgb_alpha_v1",
        "entity_id": "SPY",
        "features": {"ret_1d": 0.01, "vol_20d": 0.15},
    }
    resp = client.post("/score/", json=payload)
    assert resp.status_code == 503
