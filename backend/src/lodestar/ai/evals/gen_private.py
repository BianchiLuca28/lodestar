"""Draft private eval cases from the real ledger (design §6.5, invariant 5).

Usage: uv run python -m lodestar.ai.evals.gen_private [--n 100] [--db PATH] [--config DIR]
       [--out PATH] [--model NAME]

A stratified sample of real rows (every category represented); for each, the local LLM writes
the Telegram message the user would have sent, and the row itself is the expected answer. The
output is a *draft*: the user reads every line, fixes or deletes it, and saves it as
`evals/data/private/cases.jsonl`. Everything stays in git-ignored folders.
"""

import argparse
import random
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from lodestar.ai.evals.schema import Case, Line
from lodestar.config.models import AppConfig

PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "eval_message.md"
REPO_ROOT = Path(__file__).resolve().parents[5]
SENT_TIME = time(21, 0)  # evening of the transaction day, so "today" is the row's date


@dataclass(frozen=True)
class Row:
    id: int
    date: date
    amount_cents: int
    from_account: str | None
    to_account: str | None
    category: str
    subcategory: str | None
    note: str | None
    tag: str | None


def sample_rows(db: Path, n: int, seed: int = 0) -> list[Row]:
    """n rows, at least one per category, the rest proportional to category size."""
    with sqlite3.connect(db) as conn:
        rows = [
            Row(r[0], date.fromisoformat(r[1]), *r[2:])
            for r in conn.execute(
                "SELECT id, date, amount_cents, from_account, to_account, category,"
                " subcategory, note, tag FROM transactions"
                " WHERE source != 'adjustment' ORDER BY id"
            )
        ]
    rng = random.Random(seed)
    by_category: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        by_category[row.category].append(row)
    for group in by_category.values():
        rng.shuffle(group)
    picked = [group.pop() for group in by_category.values()][:n]  # one per category first
    rest = [row for group in by_category.values() for row in group]
    rng.shuffle(rest)  # a uniform draw of the rest keeps big categories proportionally big
    picked += rest[: max(0, n - len(picked))]
    return sorted(picked, key=lambda r: r.id)


def _prompt(row: Row, config: AppConfig) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8").partition("\n")[2].strip()
    accounts = config.accounts
    default = next((a for a in accounts if a.is_default), accounts[0]).name
    cash = next((a.name for a in accounts if a.type == "cash"), default)
    return template.format(
        default_account=default,
        cash_account=cash,
        amount=f"{Decimal(row.amount_cents) / 100:.2f}",
        from_account=row.from_account or "none",
        to_account=row.to_account or "none",
        category=row.category,
        subcategory=row.subcategory or "none",
        note=row.note or "none",
    )


def generate(
    model: BaseChatModel, config: AppConfig, db: Path, n: int, seed: int = 0
) -> list[Case]:
    zone = ZoneInfo(config.settings.timezone)
    cases = []
    for row in sample_rows(db, n, seed):
        message = str(model.invoke([HumanMessage(content=_prompt(row, config))]).content).strip()
        expected = Line(
            date=row.date,
            amount=Decimal(row.amount_cents) / 100,
            from_account=row.from_account,
            to_account=row.to_account,
            category=row.category,
            subcategory=row.subcategory,
            note=row.note,
            tag=row.tag,
        )
        cases.append(
            Case(
                id=f"real-{row.id}",
                message=message.strip('"'),
                sent_at=datetime.combine(row.date, SENT_TIME, zone),
                source_id=row.id,
                expected=[expected],
            )
        )
    return cases


def main() -> None:
    from lodestar.adapters.llm import chat_model
    from lodestar.config.loader import load_config
    from lodestar.config.settings import Settings

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "data" / "lodestar.db")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "config")
    parser.add_argument(
        "--out", type=Path, default=REPO_ROOT / "evals" / "data" / "private" / "cases.draft.jsonl"
    )
    parser.add_argument("--model", help="override models.parse")
    args = parser.parse_args()
    config = load_config(args.config)
    name = args.model or config.settings.models.parse
    model = chat_model(Settings.from_config(config).llm_base_url, name)
    cases = generate(model, config, args.db, args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "".join(c.model_dump_json(exclude_none=True) + "\n" for c in cases), encoding="utf-8"
    )
    print(f"Wrote {len(cases)} draft cases to {args.out}")
    print("Read every line, fix or delete it, then save the file as cases.jsonl next to it.")


if __name__ == "__main__":
    main()
