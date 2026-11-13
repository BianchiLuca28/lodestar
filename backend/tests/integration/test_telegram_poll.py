from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from lodestar.adapters.db.engine import make_engine, migrate
from lodestar.adapters.db.inbound_repo import InboundRepository
from lodestar.adapters.telegram import HttpTelegramClient
from lodestar.jobs.telegram_poll import GAP_WARNING, RECEIVED, poll_once

USER = 42
NOW = datetime(2026, 3, 14, 19, 0, tzinfo=UTC)


class FakeClient:
    def __init__(self, updates: list[dict[str, Any]]) -> None:
        self.updates = updates
        self.offsets: list[int | None] = []
        self.sent: list[tuple[int, str]] = []

    def get_updates(self, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        self.offsets.append(offset)
        return [u for u in self.updates if offset is None or u["update_id"] >= offset]

    def send_message(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))


def text(update_id: int, body: str, user: int = USER) -> dict[str, Any]:
    msg = {"message_id": update_id, "from": {"id": user}, "chat": {"id": user}, "date": 1773512400}
    return {"update_id": update_id, "message": msg | {"text": body}}


@pytest.fixture
def repo(tmp_path: Path) -> InboundRepository:
    db = tmp_path / "lodestar.db"
    migrate(db)
    return InboundRepository(make_engine(db))


def test_stores_messages_from_the_user_and_replies(repo: InboundRepository) -> None:
    client = FakeClient([text(1, "pizza 12€"), text(2, "benzina 50")])
    assert poll_once(client, repo, USER, NOW) == 2
    assert [m.text for m in repo.pending()] == ["pizza 12€", "benzina 50"]
    assert client.sent == [(USER, RECEIVED), (USER, RECEIVED)]
    assert repo.last_poll_at() == NOW


def test_other_senders_are_dropped_but_the_offset_moves_on(repo: InboundRepository) -> None:
    client = FakeClient([text(1, "spam", user=99)])
    assert poll_once(client, repo, USER, NOW) == 0
    assert repo.pending() == []
    assert client.sent == []
    poll_once(client, repo, USER, NOW)
    assert client.offsets == [None, 2]


def test_the_same_update_twice_is_stored_once(repo: InboundRepository) -> None:
    client = FakeClient([text(1, "pizza")])
    poll_once(client, repo, USER, NOW)
    client.offsets.clear()
    repo_again = poll_once(FakeClient([text(1, "pizza")]), repo, USER, NOW)
    assert repo_again == 0
    assert len(repo.pending()) == 1


def test_warns_once_after_more_than_a_day_off(repo: InboundRepository) -> None:
    poll_once(FakeClient([]), repo, USER, NOW)
    later = NOW + timedelta(hours=25)
    client = FakeClient([])
    poll_once(client, repo, USER, later)
    assert client.sent == [(USER, GAP_WARNING)]
    poll_once(client, repo, USER, later + timedelta(minutes=1))
    assert client.sent == [(USER, GAP_WARNING)]


def test_no_warning_on_the_very_first_poll(repo: InboundRepository) -> None:
    client = FakeClient([])
    poll_once(client, repo, USER, NOW)
    assert client.sent == []


@respx.mock
def test_http_client_calls_the_bot_api() -> None:
    base = "https://api.telegram.org/botTOKEN"
    updates = respx.post(f"{base}/getUpdates").mock(
        return_value=httpx.Response(200, json={"ok": True, "result": [text(1, "x")]})
    )
    send = respx.post(f"{base}/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True, "result": {}})
    )
    client = HttpTelegramClient("TOKEN")
    assert client.get_updates(offset=5, timeout=0)[0]["update_id"] == 1
    client.send_message(42, "ciao")
    assert b'"offset":5' in updates.calls[0].request.content
    assert b'"chat_id":42' in send.calls[0].request.content
