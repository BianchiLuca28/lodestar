"""One inbound message → proposed ledger lines (design §6.1).

context → extract → validate → (retry extract once with the errors) → finish.
The LLM only extracts; every check is code. A second failure still yields lines, with a
review note, so the user decides in the Inbox (drafts first, invariant 1).
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import TypedDict
from zoneinfo import ZoneInfo

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from lodestar.ai.schemas import Extraction, ProposedLine
from lodestar.config.catalog import catalog_of
from lodestar.config.models import AppConfig
from lodestar.domain.errors import FieldError
from lodestar.domain.ledger import Catalog, LineInput, validate_line

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "parse_message.md"
MAX_ATTEMPTS = 2


def _prompt() -> tuple[str, str]:
    first, _, body = PROMPT_PATH.read_text(encoding="utf-8").partition("\n")
    return first.removeprefix("version:").strip(), body.strip()


PROMPT_VERSION, PROMPT_TEMPLATE = _prompt()


@dataclass(frozen=True)
class ParseContext:
    catalog: Catalog
    accounts: Sequence[tuple[str, str]]  # (name, type)
    categories: Sequence[tuple[str, Sequence[str]]]
    default_account: str
    cash_account: str
    timezone: str = "Europe/Rome"
    trip_tag: str | None = None

    @classmethod
    def from_config(cls, config: AppConfig, trip_tag: str | None = None) -> "ParseContext":
        accounts = config.accounts
        default = next((a for a in accounts if a.is_default), accounts[0]).name
        cash = next((a.name for a in accounts if a.type == "cash"), default)
        return cls(
            catalog=catalog_of(config),
            accounts=[(a.name, a.type) for a in accounts],
            categories=[(c.name, c.subcategories) for c in config.categories],
            default_account=default,
            cash_account=cash,
            timezone=config.settings.timezone,
            trip_tag=trip_tag,
        )


@dataclass(frozen=True)
class ParseResult:
    lines: list[LineInput]
    review_note: str | None
    attempts: int
    prompt_version: str = field(default=PROMPT_VERSION)


class State(TypedDict, total=False):
    messages: list[BaseMessage]
    today: date
    lines: list[ProposedLine]
    errors: list[str]
    attempts: int


def _system_prompt(ctx: ParseContext, today: date) -> str:
    trip = (
        f'A trip is active: set tag "{ctx.trip_tag}" on every line unless the message says otherwise.'
        if ctx.trip_tag
        else "No trip is active: leave tag null unless the message gives one."
    )
    return PROMPT_TEMPLATE.format(
        today=f"{today.isoformat()} ({today.strftime('%A')})",
        accounts="\n".join(f"- {name} ({kind})" for name, kind in ctx.accounts),
        default_account=ctx.default_account,
        cash_account=ctx.cash_account,
        categories="\n".join(
            f"- {name}: {', '.join(subs) if subs else '(no subcategories)'}"
            for name, subs in ctx.categories
        ),
        trip=trip,
    )


def to_line_input(line: ProposedLine) -> LineInput:
    return LineInput(
        date=line.date,
        amount=line.amount,
        from_account=line.from_account or None,
        to_account=line.to_account or None,
        category=line.category,
        subcategory=line.subcategory or None,
        note=line.note or None,
        tag=line.tag or None,
        exclude_from_stats=False,
    )


def check(lines: Sequence[ProposedLine], catalog: Catalog, today: date) -> list[str]:
    """Every problem with the proposed lines, in words the model (and the user) can act on."""
    if not lines:
        return ["no lines: the message must produce at least one line"]
    errors = []
    for number, line in enumerate(lines, start=1):
        if line.date > today:
            errors.append(f"line {number}: date {line.date} is in the future (today is {today})")
        try:
            validate_line(to_line_input(line), catalog)
        except FieldError as exc:
            errors.append(f"line {number}: {exc}")
    return errors


def _parse_answer(content: str) -> list[ProposedLine]:
    text = content.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("the answer is not JSON")
    return Extraction.model_validate(json.loads(text[start : end + 1])).lines


def build_graph(model: BaseChatModel, ctx: ParseContext):  # type: ignore[no-untyped-def]
    def extract(state: State) -> State:
        reply = model.invoke(state["messages"])
        content = str(reply.content)
        messages = [*state["messages"], AIMessage(content=content)]
        attempts = state.get("attempts", 0) + 1
        try:
            lines = _parse_answer(content)
        except (ValueError, ValidationError) as exc:
            return {
                "messages": messages,
                "lines": [],
                "errors": [f"invalid JSON: {exc}"],
                "attempts": attempts,
            }
        return {"messages": messages, "lines": lines, "errors": [], "attempts": attempts}

    def validate(state: State) -> State:
        if state["errors"]:
            return {}
        return {"errors": check(state["lines"], ctx.catalog, state["today"])}

    def retry(state: State) -> State:
        feedback = "Your answer has these problems:\n" + "\n".join(
            f"- {e}" for e in state["errors"]
        )
        feedback += "\nAnswer again with the corrected JSON only."
        return {"messages": [*state["messages"], HumanMessage(content=feedback)]}

    def route(state: State) -> str:
        if not state["errors"] or state["attempts"] >= MAX_ATTEMPTS:
            return END
        return "retry"

    graph = StateGraph(State)
    graph.add_node("extract", extract)
    graph.add_node("validate", validate)
    graph.add_node("retry", retry)
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "validate")
    graph.add_conditional_edges("validate", route, {"retry": "retry", END: END})
    graph.add_edge("retry", "extract")
    return graph.compile()


def parse_message(
    model: BaseChatModel, ctx: ParseContext, message: str, sent_at: datetime
) -> ParseResult:
    today = sent_at.astimezone(ZoneInfo(ctx.timezone)).date()
    messages: list[BaseMessage] = [
        SystemMessage(content=_system_prompt(ctx, today)),
        HumanMessage(content=message),
    ]
    final = build_graph(model, ctx).invoke({"messages": messages, "today": today})
    errors: list[str] = final.get("errors", [])
    return ParseResult(
        lines=[to_line_input(line) for line in final.get("lines", [])],
        review_note="\n".join(errors) if errors else None,
        attempts=final.get("attempts", 0),
    )
