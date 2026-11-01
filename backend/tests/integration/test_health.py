from importlib.metadata import version

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from lodestar.config.settings import Settings
from lodestar.main import create_app

BASE_URL = "http://llm.test:11434"
MODELS_URL = f"{BASE_URL}/v1/models"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings(llm_base_url=BASE_URL)))


@respx.mock
def test_health_reports_ok_version_and_reachable_llm(client: TestClient) -> None:
    respx.get(MODELS_URL).mock(return_value=httpx.Response(200, json={"data": []}))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": version("lodestar"),
        "llm": {"reachable": True, "base_url": BASE_URL},
    }


@respx.mock
def test_health_reports_llm_unreachable_when_connection_refused(client: TestClient) -> None:
    respx.get(MODELS_URL).mock(side_effect=httpx.ConnectError("refused"))

    body = client.get("/api/health").json()

    assert body["status"] == "ok"
    assert body["llm"] == {"reachable": False, "base_url": BASE_URL}


@respx.mock
def test_health_reports_llm_unreachable_on_timeout(client: TestClient) -> None:
    respx.get(MODELS_URL).mock(side_effect=httpx.ReadTimeout("slow"))

    assert client.get("/api/health").json()["llm"]["reachable"] is False


@respx.mock
def test_health_reports_llm_unreachable_on_error_status(client: TestClient) -> None:
    respx.get(MODELS_URL).mock(return_value=httpx.Response(500))

    assert client.get("/api/health").json()["llm"]["reachable"] is False


def test_health_schema_is_in_openapi() -> None:
    schemas = create_app(Settings(llm_base_url=BASE_URL)).openapi()["components"]["schemas"]

    assert {"HealthResponse", "LlmStatus"} <= schemas.keys()
