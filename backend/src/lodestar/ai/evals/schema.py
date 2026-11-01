"""Eval case format: an Italian message and the exact ledger lines it must produce."""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class Line(BaseModel):
    """One proposed ledger line, in the `transactions` layout (design §5)."""

    model_config = ConfigDict(frozen=True)

    date: date
    amount: Decimal
    from_account: str | None = None
    to_account: str | None = None
    category: str
    subcategory: str | None = None
    note: str | None = None
    tag: str | None = None


class Case(BaseModel):
    id: str
    message: str
    sent_at: datetime
    expected: list[Line]


def load_cases(path: Path) -> list[Case]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Case.model_validate(json.loads(raw)) for raw in lines if raw.strip()]
