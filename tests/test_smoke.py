import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic_settings")

from fastapi.testclient import TestClient

from app.main import app


def test_openapi_is_available_without_database_or_llm():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Adaptive Python Learning Engine"
