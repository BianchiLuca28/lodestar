"""The real parser behind the eval runner (`make eval ARGS=--live`)."""

from datetime import datetime
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from sqlmodel import Session

from lodestar.adapters.db.engine import db_path, make_engine, migrate
from lodestar.adapters.db.examples_index import ExampleIndex
from lodestar.adapters.db.transactions_repo import new_row
from lodestar.adapters.embeddings import Embedder
from lodestar.adapters.loaders.csv_loader import CsvLoader
from lodestar.ai.evals.schema import Line
from lodestar.ai.graphs.parse_message import (
    PROMPT_VERSION,
    ParseContext,
    Retriever,
    parse_message,
)
from lodestar.config.catalog import catalog_of
from lodestar.config.loader import load_config


class GraphPredictor:
    def __init__(
        self,
        model: BaseChatModel,
        model_name: str,
        ctx: ParseContext,
        retriever: Retriever | None = None,
    ) -> None:
        self._model = model
        self._ctx = ctx
        self._retriever = retriever
        self.model = model_name
        self.prompt_version = f"parse-v{PROMPT_VERSION}"

    def predict(self, message: str, sent_at: datetime) -> list[Line]:
        result = parse_message(self._model, self._ctx, message, sent_at, self._retriever)
        return [
            Line(
                date=line.date,
                amount=line.amount,
                from_account=line.from_account,
                to_account=line.to_account,
                category=line.category,
                subcategory=line.subcategory,
                note=line.note,
                tag=line.tag,
            )
            for line in result.lines
        ]


def fake_ledger_index(
    config_dir: Path, work_dir: Path, embedder: Embedder, model: str
) -> ExampleIndex:
    """Example index over the fake persona's ledger.csv in a throwaway DB (invariant 5)."""
    config = load_config(config_dir)
    db = db_path(work_dir)
    migrate(db)
    loaded = CsvLoader().load(config_dir / "ledger.csv", catalog_of(config))
    engine = make_engine(db)
    with Session(engine) as session:
        session.add_all([new_row(line, "import") for line in loaded.rows])
        session.commit()
    engine.dispose()
    index = ExampleIndex(db, embedder, model)
    index.sync()
    return index
