from pathlib import Path

from fastapi.testclient import TestClient

from lodestar.config.loader import load_config
from lodestar.main import create_app

EXAMPLE = Path(__file__).parents[3] / "config.example"


def test_config_endpoint_returns_accounts_and_categories() -> None:
    client = TestClient(create_app(load_config(EXAMPLE)))
    body = client.get("/api/config").json()
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
