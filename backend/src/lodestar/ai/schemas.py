"""Output schemas the LLM must fill; validated in code after every call."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ProposedLine(BaseModel):
    date: date
    amount: Decimal
    from_account: str | None = None
    to_account: str | None = None
    category: str
    subcategory: str | None = None
    note: str | None = None
    tag: str | None = None


class Extraction(BaseModel):
    lines: list[ProposedLine]
