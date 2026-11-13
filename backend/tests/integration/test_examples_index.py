from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from lodestar.adapters.db.drafts_repo import DraftRepository
from lodestar.adapters.db.examples_index import ExampleIndex
from lodestar.adapters.db.transactions_repo import new_row
from lodestar.adapters.embeddings import HashingEmbedder
from lodestar.ai.evals.graph_predictor import fake_ledger_index
from lodestar.domain.ledger import LineInput


class Counting(HashingEmbedder):
    def __init__(self) -> None:
        super().__init__()
        self.texts: list[str] = []

    def embed(self, texts: Any) -> list[list[float]]:
        self.texts.extend(texts)
        return super().embed(texts)


class Broken(HashingEmbedder):
    def embed(self, texts: Any) -> list[list[float]]:
        raise ConnectionError("ollama is off")


def line(
    note: str | None, category: str = "🍝 Ristoranti", sub: str | None = "Pizzeria"
) -> LineInput:
    return LineInput(
        date=date(2026, 3, 1),
        amount=Decimal("20.00"),
        from_account="Banca Aurora",
        to_account=None,
        category=category,
        subcategory=sub,
        note=note,
        tag=None,
        exclude_from_stats=False,
    )


def seed(app: FastAPI, *lines: LineInput) -> None:
    with Session(app.state.engine) as session:
        session.add_all([new_row(x, "manual") for x in lines])
        session.commit()


@pytest.fixture
def ledger(app: FastAPI) -> FastAPI:
    seed(
        app,
        line("Zi Nenè"),
        line("Zi Nenè"),
        line("Conad", "🥦 Spesa", "Supermercato"),
        line("Esselunga", "🥦 Spesa", "Supermercato"),
        line(None),
    )
    return app


def test_sync_embeds_noted_transactions_once(ledger: FastAPI) -> None:
    embedder = Counting()
    index = ExampleIndex(ledger.state.db_path, embedder, "fake")
    assert index.sync() == 4
    assert index.sync() == 0
    assert len(embedder.texts) == 4


def test_a_new_embedding_model_rebuilds_the_index(ledger: FastAPI) -> None:
    ExampleIndex(ledger.state.db_path, HashingEmbedder(), "a").sync()
    assert ExampleIndex(ledger.state.db_path, HashingEmbedder(), "b").sync() == 4


def test_nearest_finds_the_similar_note_without_duplicates(ledger: FastAPI) -> None:
    index = ExampleIndex(ledger.state.db_path, HashingEmbedder(), "fake")
    index.sync()
    examples = index.nearest("zi nene 30", k=2)
    assert examples[0].note == "Zi Nenè" and examples[0].subcategory == "Pizzeria"
    assert [e.note for e in examples].count("Zi Nenè") == 1
    assert len(examples) == 2


def test_approving_a_draft_adds_it_to_the_index(app: FastAPI) -> None:
    drafts = DraftRepository(app.state.engine)
    draft = drafts.create([line("Da Michele")], source="telegram", origin_text="michele 20")
    assert TestClient(app).post(f"/api/drafts/{draft.draft.id}/approve").status_code == 200
    [example] = app.state.examples.nearest("michele", k=1)
    assert example.note == "Da Michele"


def test_approval_succeeds_when_the_embedder_is_down(app: FastAPI) -> None:
    app.state.examples = ExampleIndex(app.state.db_path, Broken(), "fake")
    drafts = DraftRepository(app.state.engine)
    draft = drafts.create([line("Da Michele")], source="telegram", origin_text="michele 20")
    assert TestClient(app).post(f"/api/drafts/{draft.draft.id}/approve").status_code == 200
    assert TestClient(app).get("/api/transactions").json()["total"] == 1


def test_eval_index_is_built_from_the_fake_ledger(tmp_path: Path) -> None:
    config = Path(__file__).parents[3] / "config.example"
    index = fake_ledger_index(config, tmp_path, HashingEmbedder(), "fake")
    [example] = index.nearest("Conad", k=1)
    assert example.note == "Conad" and example.category == "🥦 Spesa"
