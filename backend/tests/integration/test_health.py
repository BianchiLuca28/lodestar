from importlib.metadata import version

from fastapi.testclient import TestClient

from lodestar.main import create_app


def test_health_reports_ok_and_package_version() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": version("lodestar")}


def test_health_schema_is_in_openapi() -> None:
    schema = create_app().openapi()

    assert "HealthResponse" in schema["components"]["schemas"]
