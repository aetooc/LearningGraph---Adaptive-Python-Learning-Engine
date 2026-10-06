import runpy

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic_settings")

from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings


def test_openapi_is_available_without_database_or_llm():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Adaptive Python Learning Engine"


def test_public_frontend_can_preflight_requests_and_other_origins_are_rejected(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://learninggraph.vercel.app"]')
    get_settings.cache_clear()
    try:
        # Build a separate app instance without changing the shared test app.
        deployment_app = runpy.run_module("app.main", run_name="deployment_cors_test")["app"]
        with TestClient(deployment_app) as client:
            headers = {
                "Origin": "https://learninggraph.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            }
            allowed = client.options("/learners", headers=headers)
            assert allowed.status_code == 200
            assert allowed.headers["access-control-allow-origin"] == headers["Origin"]
            denied = client.options("/learners", headers={**headers, "Origin": "https://other.example.com"})
            assert denied.status_code == 400
            assert "access-control-allow-origin" not in denied.headers
    finally:
        get_settings.cache_clear()
