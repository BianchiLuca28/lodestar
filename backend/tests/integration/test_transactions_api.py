import sqlite3
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

URL = "/api/transactions"


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def payload(**kw: Any) -> dict[str, Any]:
    base = {
        "date": "2026-03-14",
        "amount": "12.50",
        "from_account": "Banca Aurora",
        "category": "🍝 Ristoranti",
        "subcategory": "Pizzeria",
        "note": "Pizza con Paolo",
    }
    return base | kw


def create(client: TestClient, **kw: Any) -> dict[str, Any]:
    response = client.post(URL, json=payload(**kw))
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def test_create_returns_line_with_direction_and_manual_source(client: TestClient) -> None:
    body = create(client, tag="vacanza", exclude_from_stats=True)
    assert body["id"] > 0
    assert body["amount"] == "12.50"
    assert body["direction"] == "expense"
    assert body["source"] == "manual"
    assert body["tag"] == "vacanza"
    assert body["exclude_from_stats"] is True


def test_transfer_and_income_directions(client: TestClient) -> None:
    transfer = create(client, to_account="Broker Orsa", category="📊 Investimenti", subcategory="ETF")
    income = create(client, from_account=None, to_account="Banca Aurora")
    assert transfer["direction"] == "transfer"
    assert income["direction"] == "income"


def test_list_newest_first_with_total(client: TestClient) -> None:
    create(client, date="2026-01-01")
    create(client, date="2026-03-01")
    create(client, date="2026-02-01")
    body = client.get(URL).json()
    assert body["total"] == 3
    assert [i["date"] for i in body["items"]] == ["2026-03-01", "2026-02-01", "2026-01-01"]


def test_pagination(client: TestClient) -> None:
    for day in range(1, 6):
        create(client, date=f"2026-01-0{day}")
    body = client.get(URL, params={"limit": 2, "offset": 2}).json()
    assert body["total"] == 5
    assert [i["date"] for i in body["items"]] == ["2026-01-03", "2026-01-02"]


@pytest.mark.parametrize(
    ("params", "expected_notes"),
    [
        ({"date_from": "2026-02-01", "date_to": "2026-02-28"}, {"feb"}),
        ({"account": "Contanti"}, {"cash"}),
        ({"account": "Broker Orsa"}, {"transfer"}),
        ({"category": "🥦 Spesa"}, {"cash"}),
        ({"tag": "lisbona"}, {"feb"}),
        ({"q": "TRANS"}, {"transfer"}),
    ],
)
def test_filters(client: TestClient, params: dict[str, str], expected_notes: set[str]) -> None:
    create(client, date="2026-01-10", note="jan")
    create(client, date="2026-02-10", note="feb", tag="lisbona")
    create(
        client,
        date="2026-03-10",
        note="cash",
        from_account="Contanti",
        category="🥦 Spesa",
        subcategory="Mercato",
    )
    create(
        client,
        date="2026-03-11",
        note="transfer",
        to_account="Broker Orsa",
        category="📊 Investimenti",
        subcategory="ETF",
    )
    items = client.get(URL, params=params).json()["items"]
    assert {i["note"] for i in items} == expected_notes


def test_patch_updates_fields_and_keeps_source(client: TestClient) -> None:
    created = create(client)
    response = client.patch(f"{URL}/{created['id']}", json={"amount": "20.00", "tag": "x"})
    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == "20.00" and body["tag"] == "x" and body["note"] == "Pizza con Paolo"
    assert body["source"] == "manual"


def test_patch_is_validated_as_a_whole(client: TestClient) -> None:
    created = create(client)
    response = client.patch(f"{URL}/{created['id']}", json={"from_account": None})
    assert response.status_code == 422
    assert response.json()["key"] == "error.missingAccount"


def test_delete(client: TestClient) -> None:
    created = create(client)
    assert client.delete(f"{URL}/{created['id']}").status_code == 204
    assert client.get(URL).json()["total"] == 0


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_unknown_id_is_404(client: TestClient, method: str) -> None:
    kwargs: dict[str, Any] = {"json": {"note": "x"}} if method == "patch" else {}
    response = getattr(client, method)(f"{URL}/999", **kwargs)
    assert response.status_code == 404
    assert response.json()["key"] == "error.notFound"


@pytest.mark.parametrize(
    ("change", "key", "field"),
    [
        ({"from_account": "Banca Fantasma"}, "error.unknownAccount", "from_account"),
        ({"category": "🛸 Ufo"}, "error.unknownCategory", "category"),
        ({"subcategory": "Cinema"}, "error.unknownSubcategory", "subcategory"),
        ({"amount": "0"}, "error.invalidAmount", "amount"),
        ({"amount": "1.005"}, "error.invalidAmount", "amount"),
        ({"from_account": None}, "error.missingAccount", "from_account"),
        ({"to_account": "Banca Aurora"}, "error.sameAccount", "to_account"),
    ],
)
def test_validation_errors(client: TestClient, change: dict[str, Any], key: str, field: str) -> None:
    response = client.post(URL, json=payload(**change))
    assert response.status_code == 422
    body = response.json()
    assert (body["key"], body["field"]) == (key, field)


def test_line_used_by_a_balance_check_cannot_be_deleted(app: FastAPI, client: TestClient) -> None:
    created = create(client, category="❓ Varie", subcategory=None)
    with sqlite3.connect(app.state.db_path) as conn:
        conn.execute(
            "INSERT INTO balance_checks (account, date, real_balance_cents,"
            " computed_balance_cents, adjustment_transaction_id, created_at)"
            " VALUES ('Banca Aurora', '2026-03-14', 0, 1250, ?, '2026-03-14T10:00:00')",
            (created["id"],),
        )
    response = client.delete(f"{URL}/{created['id']}")
    assert response.status_code == 409
    assert response.json()["key"] == "error.linkedToBalanceCheck"
