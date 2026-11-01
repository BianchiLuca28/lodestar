from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_config_endpoint_returns_accounts_and_categories(app: FastAPI) -> None:
    body = TestClient(app).get("/api/config").json()
    accounts = {a["name"]: a for a in body["accounts"]}
    assert accounts["Banca Aurora"] == {
        "name": "Banca Aurora",
        "type": "bank",
        "bucket": "P1",
        "is_default": True,
    }
    categories = {c["name"]: c for c in body["categories"]}
    assert categories["🍝 Ristoranti"]["discretionary"] is True
    assert "Pizzeria" in categories["🍝 Ristoranti"]["subcategories"]
