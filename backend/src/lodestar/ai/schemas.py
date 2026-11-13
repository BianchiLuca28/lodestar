"""Output schemas the LLM must fill; validated in code after every call."""

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel


class ProposedLine(BaseModel):
    # The LLM copies the date words verbatim ("ieri", "giovedì", "il 2 novembre", or null);
    # `date` is then set by code (domain/dates.py). A date the model computes is ignored.
    date_text: str | None = None
    date: dt.date | None = None
    amount: Decimal
    from_account: str | None = None
    to_account: str | None = None
    category: str
    subcategory: str | None = None
    note: str | None = None
    tag: str | None = None


class Extraction(BaseModel):
    lines: list[ProposedLine]
