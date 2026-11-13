from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

URL = "/api/drafts"


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def line(**kw: Any) -> dict[str, Any]:
    base = {
        "date": "2026-03-14",
        "amount": "50.00",
        "from_account": "Banca Aurora",
        "category": "🍝 Ristoranti",
        "subcategory": "Pizzeria",
        "note": "Cena",
    }
    return base | kw


def create(client: TestClient, lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    body = {
        "origin_text": "Ristorante 50€, l'amico me ne ha ridati 25",
        "source": "telegram",
        "lines": lines
        or [line(), line(amount="25.00", from_account=None, to_account="Banca Aurora")],
    }
    response = client.post(URL, json=body)
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def test_created_draft_is_listed_as_pending(client: TestClient) -> None:
    draft = create(client)
    assert draft["status"] == "pending"
    assert draft["version"] == 1
    assert len(draft["lines"]) == 2
    items = client.get(URL, params={"status": "pending"}).json()
    assert [d["id"] for d in items] == [draft["id"]]
    assert client.get(URL, params={"status": "approved"}).json() == []


def test_possible_duplicate_points_at_existing_transaction(client: TestClient) -> None:
    tx = client.post("/api/transactions", json=line(date="2026-03-13")).json()
    draft = create(client)
    assert draft["lines"][0]["possible_duplicates"] == [tx["id"]]
    assert draft["lines"][1]["possible_duplicates"] == []


def test_edit_creates_a_new_version_and_keeps_the_old_one(client: TestClient) -> None:
    draft = create(client)
    response = client.put(f"{URL}/{draft['id']}/lines", json={"lines": [line(amount="48.00")]})
    assert response.status_code == 200, response.text
    assert response.json()["version"] == 2
    full = client.get(f"{URL}/{draft['id']}").json()
    assert [v["version"] for v in full["versions"]] == [1, 2]
    assert len(full["versions"][0]["lines"]) == 2
    assert full["lines"][0]["amount"] == "48.00"


def test_approve_writes_all_lines_with_the_draft_source(client: TestClient) -> None:
    draft = create(client)
    response = client.post(f"{URL}/{draft['id']}/approve")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "approved"
    items = client.get("/api/transactions").json()["items"]
    assert len(items) == 2
    assert {i["source"] for i in items} == {"telegram"}
    again = client.post(f"{URL}/{draft['id']}/approve")
    assert again.status_code == 409


def test_invalid_line_blocks_creation(client: TestClient) -> None:
    response = client.post(
        URL, json={"origin_text": "x", "source": "telegram", "lines": [line(category="Nope")]}
    )
    assert response.status_code == 422


def test_reject_writes_nothing_and_freezes_the_draft(client: TestClient) -> None:
    draft = create(client)
    assert client.post(f"{URL}/{draft['id']}/reject").json()["status"] == "rejected"
    assert client.get("/api/transactions").json()["total"] == 0
    assert client.put(f"{URL}/{draft['id']}/lines", json={"lines": [line()]}).status_code == 409


def test_unknown_draft_is_404(client: TestClient) -> None:
    assert client.get(f"{URL}/999").status_code == 404
