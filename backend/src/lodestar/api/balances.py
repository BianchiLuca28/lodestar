"""Account balances and balance checks (design §2 F5, §5 balance_checks, §8 Movimenti)."""

import datetime as dt
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from lodestar.adapters.db.balance_checks_repo import BalanceCheckRepository, StoredCheck
from lodestar.adapters.db.transactions_repo import TransactionRepository
from lodestar.api.transactions import ERRORS, TransactionOut, to_out
from lodestar.config.models import AppConfig
from lodestar.domain.balances import adjustment_for, balance_of, gap_between
from lodestar.domain.errors import FieldError, InvalidAmount
from lodestar.domain.money import from_cents, quantize, to_cents
from lodestar.domain.ports import LedgerTotals

router = APIRouter(prefix="/api", tags=["balances"], responses=ERRORS)


class AccountBalance(BaseModel):
    account: str
    balance: Decimal


class BalanceCheckIn(BaseModel):
    account: str
    date: dt.date
    real_balance: Decimal


class BalancePreview(BaseModel):
    computed: Decimal
    gap: Decimal


class BalanceCheckOut(BaseModel):
    id: int
    account: str
    date: dt.date
    real_balance: Decimal
    computed_balance: Decimal
    gap: Decimal
    adjustment: TransactionOut | None


def get_config(request: Request) -> AppConfig:
    config: AppConfig = request.app.state.config
    return config


def get_ledger(request: Request) -> TransactionRepository:
    return TransactionRepository(request.app.state.engine)


def get_checks(request: Request) -> BalanceCheckRepository:
    return BalanceCheckRepository(request.app.state.engine)


Config = Annotated[AppConfig, Depends(get_config)]
Ledger = Annotated[TransactionRepository, Depends(get_ledger)]
Checks = Annotated[BalanceCheckRepository, Depends(get_checks)]


def _computed(ledger: LedgerTotals, account: str, on: dt.date) -> Decimal:
    return balance_of(ledger.totals(account, on))


def _validate(data: BalanceCheckIn, config: AppConfig) -> None:
    if data.account not in {a.name for a in config.accounts}:
        raise FieldError("error.unknownAccount", "account", f"unknown account {data.account!r}")
    try:
        to_cents(data.real_balance)
    except InvalidAmount as exc:
        raise FieldError("error.invalidAmount", "real_balance", str(exc)) from exc


def _check_out(stored: StoredCheck) -> BalanceCheckOut:
    check = stored.check
    assert check.id is not None
    real = from_cents(check.real_balance_cents)
    computed = from_cents(check.computed_balance_cents)
    return BalanceCheckOut(
        id=check.id,
        account=check.account,
        date=check.date,
        real_balance=real,
        computed_balance=computed,
        gap=gap_between(real, computed),
        adjustment=to_out(stored.adjustment) if stored.adjustment else None,
    )


@router.get("/accounts/balances")
def account_balances(
    config: Config, ledger: Ledger, date: dt.date | None = None
) -> list[AccountBalance]:
    on = date or dt.date.today()
    return [
        AccountBalance(account=a.name, balance=_computed(ledger, a.name, on))
        for a in config.accounts
    ]


@router.post("/balance-checks/preview")
def preview_balance_check(data: BalanceCheckIn, config: Config, ledger: Ledger) -> BalancePreview:
    _validate(data, config)
    computed = _computed(ledger, data.account, data.date)
    return BalancePreview(computed=computed, gap=gap_between(quantize(data.real_balance), computed))


@router.post("/balance-checks", status_code=status.HTTP_201_CREATED)
def create_balance_check(
    data: BalanceCheckIn, config: Config, ledger: Ledger, checks: Checks
) -> BalanceCheckOut:
    _validate(data, config)
    real = quantize(data.real_balance)
    computed = _computed(ledger, data.account, data.date)
    line = adjustment_for(
        data.account,
        data.date,
        gap_between(real, computed),
        config.settings.ledger.adjustment_category,
    )
    return _check_out(checks.record(data.account, data.date, real, computed, line))


@router.get("/balance-checks")
def list_balance_checks(checks: Checks, account: str | None = None) -> list[BalanceCheckOut]:
    return [_check_out(stored) for stored in checks.history(account)]
