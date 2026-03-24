"""Integration tests for dataset-platform service."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.dataset_platform.app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "dataset-platform"


def test_list_datasets_empty():
    resp = client.get("/datasets/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_and_get_dataset():
    payload = {
        "name": "test_ds",
        "version": "1.0.0",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "universe": ["SPY"],
        "feature_names": ["ret_1d"],
    }
    create_resp = client.post("/datasets/", json=payload)
    assert create_resp.status_code == 201
    record = create_resp.json()
    assert record["spec"]["name"] == "test_ds"

    get_resp = client.get(f"/datasets/{record['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == record["id"]


def test_get_dataset_not_found():
    resp = client.get("/datasets/nonexistent-id")
    assert resp.status_code == 404
