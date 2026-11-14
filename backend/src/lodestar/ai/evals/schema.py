"""Eval case format: an Italian message and the exact ledger lines it must produce."""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


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
    source_id: int | None = None  # private cases: the real row they came from
    trip: str | None = None  # trip mode on with this tag, as the app does during a trip
    expected: list[Line]

    @field_validator("message")
    @classmethod
    def _not_blank(cls, message: str) -> str:
        if not message.strip():
            raise ValueError("the message is empty")
        return message


def load_cases(path: Path) -> list[Case]:
    cases = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        data = json.loads(raw)
        try:
            cases.append(Case.model_validate(data))
        except ValidationError as exc:
            where = f"{path.name} line {number} (case {data.get('id', '?')})"
            raise ValueError(f"{where}: {exc}") from exc
    return cases
