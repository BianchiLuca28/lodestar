from importlib.metadata import version

import httpx
import pytest
import respx
from fastapi import FastAPI
from fastapi.testclient import TestClient

TEST_LLM_URL = "http://llm.test:11434"  # matches the settings fixture in conftest.py

MODELS_URL = f"{TEST_LLM_URL}/v1/models"


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@respx.mock
def test_health_reports_ok_version_llm_and_database(client: TestClient) -> None:
    respx.get(MODELS_URL).mock(return_value=httpx.Response(200, json={"data": []}))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": version("lodestar"),
        "llm": {"reachable": True, "base_url": TEST_LLM_URL},
        "database": {"reachable": True, "revision": "0001"},
        "backup": {"enabled": True, "last_backup": None, "folder": "backups"},
    }


@respx.mock
def test_health_reports_llm_unreachable_when_connection_refused(client: TestClient) -> None:
    respx.get(MODELS_URL).mock(side_effect=httpx.ConnectError("refused"))

    body = client.get("/api/health").json()

    assert body["status"] == "ok"
    assert body["llm"] == {"reachable": False, "base_url": TEST_LLM_URL}


@respx.mock
def test_health_reports_llm_unreachable_on_timeout(client: TestClient) -> None:
    respx.get(MODELS_URL).mock(side_effect=httpx.ReadTimeout("slow"))

    assert client.get("/api/health").json()["llm"]["reachable"] is False


@respx.mock
def test_health_reports_llm_unreachable_on_error_status(client: TestClient) -> None:
    respx.get(MODELS_URL).mock(return_value=httpx.Response(500))

    assert client.get("/api/health").json()["llm"]["reachable"] is False


def test_health_schema_is_in_openapi(app: FastAPI) -> None:
    schemas = app.openapi()["components"]["schemas"]

    assert {"HealthResponse", "LlmStatus", "DatabaseStatus"} <= schemas.keys()
