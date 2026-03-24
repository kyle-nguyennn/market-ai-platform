"""E2E smoke test: health-check all three services in sequence."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.dataset_platform.app.main import app as ds_app
from services.inference_gateway.app.main import app as ig_app
from services.eval_control_plane.app.main import app as ecp_app


@pytest.fixture(scope="module")
def ds_client():
    return TestClient(ds_app)


@pytest.fixture(scope="module")
def ig_client():
    return TestClient(ig_app)


@pytest.fixture(scope="module")
def ecp_client():
    return TestClient(ecp_app)


def test_all_services_healthy(ds_client, ig_client, ecp_client):
    for client in (ds_client, ig_client, ecp_client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
