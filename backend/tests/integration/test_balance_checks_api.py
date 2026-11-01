from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    c = TestClient(app)
    lines: list[dict[str, Any]] = [
        # Banca Aurora: +2150 salary, −720 rent, −100 to the card, −12.50 pizza on 15/03 (later)
        {
            "date": "2026-03-01",
            "amount": "2150.00",
            "to_account": "Banca Aurora",
            "category": "💰 Stipendio",
        },
        {
            "date": "2026-03-02",
            "amount": "720.00",
            "from_account": "Banca Aurora",
            "category": "🏡 Affitto",
        },
        {
            "date": "2026-03-03",
            "amount": "100.00",
            "from_account": "Banca Aurora",
            "to_account": "Carta Nebbia",
            "category": "❓ Varie",
            "exclude_from_stats": True,
        },
        {
            "date": "2026-03-15",
            "amount": "12.50",
            "from_account": "Banca Aurora",
            "category": "🍝 Ristoranti",
        },
    ]
    for line in lines:
        assert c.post("/api/transactions", json=line).status_code == 201
    return c


def balances(client: TestClient, **params: str) -> dict[str, str]:
    body = client.get("/api/accounts/balances", params=params).json()
    return {b["account"]: b["balance"] for b in body}


def test_balances_of_every_configured_account(client: TestClient) -> None:
    result = balances(client)
    assert result["Banca Aurora"] == "1317.50"
    assert result["Carta Nebbia"] == "100.00"
    assert result["Contanti"] == "0.00"
    assert len(result) == 5  # every account in config.example


def test_balances_at_a_date_include_that_day(client: TestClient) -> None:
    assert balances(client, date="2026-03-02")["Banca Aurora"] == "1430.00"
    assert balances(client, date="2026-03-15")["Banca Aurora"] == "1317.50"


def test_preview_shows_gap_without_writing(client: TestClient) -> None:
    body = client.post(
        "/api/balance-checks/preview",
        json={"account": "Banca Aurora", "date": "2026-03-10", "real_balance": "1335.00"},
    ).json()
    assert body == {"computed": "1330.00", "gap": "5.00"}
    assert client.get("/api/balance-checks").json() == []


def test_check_with_gap_creates_a_linked_adjustment(client: TestClient) -> None:
    response = client.post(
        "/api/balance-checks",
        json={"account": "Banca Aurora", "date": "2026-03-10", "real_balance": "1300.00"},
    )
    assert response.status_code == 201
    check = response.json()
    assert (check["computed_balance"], check["real_balance"], check["gap"]) == (
        "1330.00",
        "1300.00",
        "-30.00",
    )
    adjustment = check["adjustment"]
    assert adjustment["amount"] == "30.00"
    assert adjustment["direction"] == "expense"
    assert adjustment["source"] == "adjustment"
    assert adjustment["exclude_from_stats"] is True
    assert adjustment["category"] == "❓ Varie"
    assert balances(client, date="2026-03-10")["Banca Aurora"] == "1300.00"

    delete = client.delete(f"/api/transactions/{adjustment['id']}")
    assert delete.status_code == 409


def test_zero_gap_records_check_without_a_line(client: TestClient) -> None:
    check = client.post(
        "/api/balance-checks",
        json={"account": "Carta Nebbia", "date": "2026-03-10", "real_balance": "100"},
    ).json()
    assert check["gap"] == "0.00"
    assert check["adjustment"] is None
    assert client.get("/api/transactions").json()["total"] == 4


def test_history_newest_first_and_filtered(client: TestClient) -> None:
    for day, account in (
        ("2026-03-05", "Contanti"),
        ("2026-03-09", "Contanti"),
        ("2026-03-07", "Banca Aurora"),
    ):
        client.post(
            "/api/balance-checks", json={"account": account, "date": day, "real_balance": "0"}
        )
    contanti = client.get("/api/balance-checks", params={"account": "Contanti"}).json()
    assert [c["date"] for c in contanti] == ["2026-03-09", "2026-03-05"]
    assert len(client.get("/api/balance-checks").json()) == 3


@pytest.mark.parametrize(
    ("payload", "key"),
    [
        (
            {"account": "Banca Fantasma", "date": "2026-03-10", "real_balance": "1"},
            "error.unknownAccount",
        ),
        (
            {"account": "Contanti", "date": "2026-03-10", "real_balance": "1.005"},
            "error.invalidAmount",
        ),
    ],
)
def test_invalid_checks(client: TestClient, payload: dict[str, str], key: str) -> None:
    for url in ("/api/balance-checks", "/api/balance-checks/preview"):
        response = client.post(url, json=payload)
        assert response.status_code == 422
        assert response.json()["key"] == key
