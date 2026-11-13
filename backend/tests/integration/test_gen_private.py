import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from lodestar.ai.evals.gen_private import generate, sample_rows
from lodestar.ai.evals.graph_predictor import fake_ledger_db
from lodestar.config.loader import load_config
from lodestar.domain.dates import resolve_date

EXAMPLE = Path(__file__).parents[3] / "config.example"


def fake(n: int) -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter(AIMessage(content=f"msg {i}") for i in range(n)))


def test_sample_is_stratified_and_deterministic(tmp_path: Path) -> None:
    db = fake_ledger_db(EXAMPLE, tmp_path)
    rows = sample_rows(db, 30, seed=1)
    assert len(rows) == 30
    assert [r.id for r in rows] == [r.id for r in sample_rows(db, 30, seed=1)]
    with sqlite3.connect(db) as conn:
        categories = {c for (c,) in conn.execute("SELECT DISTINCT category FROM transactions")}
    sampled = Counter(r.category for r in rows)
    assert set(sampled) == categories  # every category is represented
    assert len({r.id for r in rows}) == 30


def test_cases_keep_the_real_row_as_the_expected_answer(tmp_path: Path) -> None:
    db = fake_ledger_db(EXAMPLE, tmp_path)
    config = load_config(EXAMPLE)
    cases = generate(fake(5), config, db, 5, seed=2)
    assert [c.message for c in cases] == [f"msg {i}" for i in range(5)]
    with sqlite3.connect(db) as conn:
        for case in cases:
            assert case.source_id is not None and case.id == f"real-{case.source_id}"
            note, cents, day = conn.execute(
                "SELECT note, amount_cents, date FROM transactions WHERE id = ?",
                (case.source_id,),
            ).fetchone()
            [line] = case.expected
            assert line.note == note and line.amount * 100 == cents
            assert day == line.date.isoformat()


class Recording(GenericFakeChatModel):
    prompts: list[str] = []

    def invoke(self, input: Any, *args: Any, **kwargs: Any) -> Any:  # noqa: A002
        self.prompts.append(str(input[0].content))
        return super().invoke(input, *args, **kwargs)


def test_about_a_third_of_cases_are_sent_later_and_must_say_the_date(tmp_path: Path) -> None:
    db = fake_ledger_db(EXAMPLE, tmp_path)
    model = Recording(messages=iter(AIMessage(content=f"msg {i}") for i in range(40)), prompts=[])
    cases = generate(model, load_config(EXAMPLE), db, 40, seed=4)
    late = [
        (c, p)
        for c, p in zip(cases, model.prompts, strict=True)
        if c.sent_at.date() != c.expected[0].date
    ]
    assert 6 <= len(late) <= 20
    for case, prompt in late:
        delay = (case.sent_at.date() - case.expected[0].date).days
        assert 1 <= delay <= 6
        words = re.search(r'using exactly these words: "([^"]+)"', prompt)
        assert words is not None, prompt
        assert resolve_date(words.group(1), case.sent_at.date()) == case.expected[0].date
    on_time = [
        p
        for c, p in zip(cases, model.prompts, strict=True)
        if c.sent_at.date() == c.expected[0].date
    ]
    assert all("give no date" in p for p in on_time)
