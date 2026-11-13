import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage

from lodestar.ai.graphs.parse_message import ParseContext, parse_message
from lodestar.config.loader import load_config

EXAMPLE = Path(__file__).parents[3] / "config.example"
SENT = datetime(2026, 3, 14, 19, 30, tzinfo=UTC)  # Saturday evening in Rome


class Recording(GenericFakeChatModel):
    """A fake chat model that also keeps the prompts it was given."""

    prompts: list[list[BaseMessage]] = []

    def invoke(self, input: Any, *args: Any, **kwargs: Any) -> Any:  # noqa: A002
        self.prompts.append(list(input))
        return super().invoke(input, *args, **kwargs)


def model(*answers: object) -> Recording:
    texts = [a if isinstance(a, str) else json.dumps(a) for a in answers]
    return Recording(messages=iter([AIMessage(content=t) for t in texts]), prompts=[])


def line(**kw: Any) -> dict[str, Any]:
    base = {
        "date": "2026-03-14",
        "amount": "50.00",
        "from_account": "Banca Aurora",
        "to_account": None,
        "category": "🍝 Ristoranti",
        "subcategory": "Pizzeria",
        "note": "Zi Nenè",
        "tag": None,
    }
    return base | kw


def context() -> ParseContext:
    return ParseContext.from_config(load_config(EXAMPLE))


def test_valid_answer_gives_the_lines() -> None:
    fake = model(
        {"lines": [line(), line(amount="25.00", from_account=None, to_account="Banca Aurora")]}
    )
    result = parse_message(fake, context(), "Zi Nenè 50€, Marco me ne ha ridati 25", SENT)
    assert result.review_note is None
    assert [r.amount for r in result.lines] == [Decimal("50.00"), Decimal("25.00")]
    assert result.lines[0].date == date(2026, 3, 14)
    assert len(fake.prompts) == 1


def test_invalid_category_is_retried_with_the_errors() -> None:
    fake = model({"lines": [line(category="Pizza")]}, {"lines": [line()]})
    result = parse_message(fake, context(), "pizza 50", SENT)
    assert result.review_note is None
    assert result.lines[0].category == "🍝 Ristoranti"
    retry_prompt = str(fake.prompts[1][-1].content)
    assert "unknown category 'Pizza'" in retry_prompt


def test_malformed_json_is_retried() -> None:
    fake = model("certo! ecco", {"lines": [line()]})
    assert parse_message(fake, context(), "pizza 50", SENT).review_note is None


def test_two_bad_answers_give_a_draft_flagged_for_review() -> None:
    fake = model({"lines": [line(category="Pizza")]}, {"lines": [line(category="Pizza")]})
    result = parse_message(fake, context(), "pizza 50", SENT)
    assert result.review_note is not None
    assert "Pizza" in result.review_note
    assert result.lines[0].category == "Pizza"  # kept, so the user can fix it in the Inbox
    assert len(fake.prompts) == 2


def test_a_future_date_is_rejected() -> None:
    fake = model({"lines": [line(date="2026-03-20")]}, {"lines": [line()]})
    result = parse_message(fake, context(), "pizza 50", SENT)
    assert "future" in str(fake.prompts[1][-1].content)
    assert result.lines[0].date == date(2026, 3, 14)


def test_no_lines_is_an_error() -> None:
    fake = model({"lines": []}, {"lines": []})
    assert parse_message(fake, context(), "ciao", SENT).review_note is not None


def test_prompt_gives_the_send_date_in_rome_with_its_weekday_and_the_catalog() -> None:
    late = datetime(2026, 3, 14, 23, 30, tzinfo=UTC)  # already Sunday 15 in Rome
    fake = model({"lines": [line(date="2026-03-15")]})
    parse_message(fake, context(), "ieri pizza", late)
    system = str(fake.prompts[0][0].content)
    assert "2026-03-15 (Sunday)" in system
    assert "Banca Aurora" in system
    assert "🍝 Ristoranti" in system and "Pizzeria" in system


def test_retrieved_examples_are_in_the_prompt() -> None:
    from lodestar.adapters.db.examples_index import Example

    seen: list[str] = []

    def retriever(text: str) -> list[Example]:
        seen.append(text)
        return [Example("Zi Nenè", "🍝 Ristoranti", "Pizzeria", "Banca Aurora", None)] * 7

    fake = model({"lines": [line()]})
    parse_message(fake, context(), "zi nene 30", SENT, retriever)
    system = str(fake.prompts[0][0].content)
    assert seen == ["zi nene 30"]
    assert '"Zi Nenè" → category "🍝 Ristoranti", subcategory "Pizzeria"' in system
    assert system.count('"Zi Nenè" →') == 5


def test_a_failing_retriever_parses_without_examples() -> None:
    def broken(text: str) -> list[Any]:
        raise ConnectionError("embedder is off")

    fake = model({"lines": [line()]})
    result = parse_message(fake, context(), "pizza 50", SENT, broken)
    assert result.review_note is None
    assert "No past examples" in str(fake.prompts[0][0].content)
