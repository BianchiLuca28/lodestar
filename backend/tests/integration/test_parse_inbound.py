import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from lodestar.adapters.db.drafts_repo import DraftRepository
from lodestar.adapters.db.inbound_repo import InboundRepository
from lodestar.adapters.telegram import parse_update
from lodestar.ai.graphs.parse_message import ParseContext
from lodestar.config.loader import load_config
from lodestar.jobs.parse_inbound import parse_pending

EXAMPLE = Path(__file__).parents[3] / "config.example"
NOW_TS = 1773516600  # 2026-03-14 19:30 UTC


def update(update_id: int, text: str) -> dict[str, Any]:
    message = {"message_id": update_id, "from": {"id": 42}, "chat": {"id": 42}, "date": NOW_TS}
    return {"update_id": update_id, "message": message | {"text": text}}


def answer(**kw: Any) -> str:
    line = {
        "date": "2026-03-14",
        "amount": "50.00",
        "from_account": "Banca Aurora",
        "to_account": None,
        "category": "🍝 Ristoranti",
        "subcategory": "Pizzeria",
        "note": "Zi Nenè",
        "tag": None,
    }
    return json.dumps({"lines": [line | kw]})


def fake(*answers: str) -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter([AIMessage(content=a) for a in answers]))


class Broken(GenericFakeChatModel):
    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        raise ConnectionError("ollama is off")


@pytest.fixture
def ctx() -> ParseContext:
    return ParseContext.from_config(load_config(EXAMPLE))


def store(app: FastAPI, *updates: dict[str, Any]) -> InboundRepository:
    inbound = InboundRepository(app.state.engine)
    for raw in updates:
        parsed = parse_update(raw)
        assert parsed is not None
        inbound.add(parsed, raw, parsed.sent_at)
    return inbound


def test_pending_message_becomes_a_linked_draft(app: FastAPI, ctx: ParseContext) -> None:
    inbound = store(app, update(1, "Zi Nenè 50"))
    drafts = DraftRepository(app.state.engine)

    assert parse_pending(fake(answer()), ctx, inbound, drafts) == 1

    assert inbound.pending() == []
    [draft] = drafts.by_status("pending")
    assert draft.draft.source == "telegram"
    assert draft.draft.origin_text == "Zi Nenè 50"
    assert draft.draft.inbound_message_id is not None
    assert draft.draft.review_note is None
    assert draft.lines[0].amount == 50


def test_llm_down_leaves_the_message_pending(app: FastAPI, ctx: ParseContext) -> None:
    inbound = store(app, update(1, "pizza"))
    drafts = DraftRepository(app.state.engine)
    assert parse_pending(Broken(messages=iter([])), ctx, inbound, drafts) == 0
    assert len(inbound.pending()) == 1
    assert drafts.by_status(None) == []


def test_flagged_draft_shows_its_note_and_cannot_be_approved_until_fixed(
    app: FastAPI, ctx: ParseContext
) -> None:
    inbound = store(app, update(1, "pizza"))
    drafts = DraftRepository(app.state.engine)
    bad = answer(category="Pizza")
    parse_pending(fake(bad, bad), ctx, inbound, drafts)

    client = TestClient(app)
    [item] = client.get("/api/drafts", params={"status": "pending"}).json()
    assert "Pizza" in item["review_note"]
    assert client.post(f"/api/drafts/{item['id']}/approve").status_code == 422
    assert client.get("/api/transactions").json()["total"] == 0
