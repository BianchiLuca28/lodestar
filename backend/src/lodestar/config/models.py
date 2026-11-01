"""Pydantic models for the YAML files in config/ (design §9).

Every model forbids unknown fields, so a typo in a key fails loudly at startup.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Money = Annotated[Decimal, Field(ge=0, decimal_places=2)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# settings.yaml


class LlmConfig(Strict):
    base_url: str = Field(pattern=r"^https?://")


class ModelsConfig(Strict):
    parse: str
    chat: str
    vision: str | None = None
    embed: str


class BackupTarget(Strict):
    kind: Literal["folder", "s3"]
    enabled: bool = False
    path: str | None = None
    bucket: str | None = None
    region: str | None = None


class BackupConfig(Strict):
    schedule: Literal["daily"] = "daily"
    targets: list[BackupTarget] = []


class NotificationsConfig(Strict):
    telegram: bool = False
    digest_day: int = Field(default=1, ge=1, le=28)
    quiet_hours: list[str] = []


class LedgerConfig(Strict):
    adjustment_category: str  # category of the lines that close a balance-check gap


class SettingsFile(Strict):
    locale: Literal["it", "en"] = "it"
    currency: Literal["EUR"] = "EUR"
    timezone: str = "Europe/Rome"
    llm: LlmConfig
    models: ModelsConfig
    ledger: LedgerConfig
    backup: BackupConfig = BackupConfig()
    notifications: NotificationsConfig = NotificationsConfig()


# accounts.yaml, categories.yaml, buckets.yaml


class Account(Strict):
    name: str
    type: Literal["cash", "bank", "broker", "postal"]
    bucket: str
    is_default: bool = False


class AccountsFile(Strict):
    accounts: list[Account] = Field(min_length=1)


class Category(Strict):
    name: str
    discretionary: bool
    subcategories: list[str] = []


class CategoriesFile(Strict):
    categories: list[Category] = Field(min_length=1)


class Bucket(Strict):
    id: str
    name: str
    purpose: str
    risk: str
    target: Any = None  # a number, a {min, max} range or {months_of_spending}
    monthly_contribution: Money
    horizon: date | str
    expected_house_date: date | None = None


class BucketsFile(Strict):
    buckets: list[Bucket] = Field(min_length=1)


# rules.yaml (design §6.2): one model per kind


class RuleBase(Strict):
    plan_section: list[str] = Field(min_length=1)


class DiscretionaryCap(RuleBase):
    kind: Literal["discretionary_cap"]
    limit: Money
    period: Literal["month"] = "month"
    net_of_refunds: bool = True


class P1Range(RuleBase):
    kind: Literal["p1_range"]
    account: str
    min: Money
    max: Money


class SafetyValve(RuleBase):
    kind: Literal["safety_valve"]
    account: str
    below: Money
    reduced_transfer: dict[str, Money]


class SurplusDestination(Strict):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    bucket: str
    from_: date | None = Field(default=None, alias="from")
    until: date | None = None


class Surplus(RuleBase):
    kind: Literal["surplus"]
    account: str
    above: Money
    keep: Money
    when: Literal["quarter_end"] = "quarter_end"
    destination: list[SurplusDestination] = Field(min_length=1)


class Transfer(Strict):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    from_: str = Field(alias="from")
    to: str
    amount: Money
    by_day: int = Field(ge=1, le=28)


class SavingsPlan(Strict):
    instrument: str
    amount: Money
    by_day: int = Field(ge=1, le=28)
    start: date | None = None


class Contributions(RuleBase):
    kind: Literal["contributions"]
    transfer: Transfer
    savings_plan: SavingsPlan | None = None


class QuarterlyOrder(RuleBase):
    kind: Literal["quarterly_order"]
    bucket: str
    months: list[int] = Field(min_length=1)


class MaturityReinvestment(RuleBase):
    kind: Literal["maturity_reinvestment"]
    bucket: str
    within_days: int = Field(gt=0)


class P3Horizon(RuleBase):
    kind: Literal["p3_horizon"]
    bucket: str
    switch_to: str
    months_before_house_date: int = Field(gt=0)


class Trajectory(RuleBase):
    kind: Literal["trajectory"]
    bucket: str
    warning_below: Money


class EmergencyFund(RuleBase):
    kind: Literal["emergency_fund"]
    bucket: str
    months_of_spending: int = Field(gt=0)
    average_over_months: int = Field(gt=0)


class NeverTouch(RuleBase):
    kind: Literal["never_touch"]
    buckets: list[str] = Field(min_length=1)


class P4ReviewThreshold(RuleBase):
    kind: Literal["p4_review_threshold"]
    bucket: str
    above: Money


Rule = Annotated[
    DiscretionaryCap
    | P1Range
    | SafetyValve
    | Surplus
    | Contributions
    | QuarterlyOrder
    | MaturityReinvestment
    | P3Horizon
    | Trajectory
    | EmergencyFund
    | NeverTouch
    | P4ReviewThreshold,
    Field(discriminator="kind"),
]


class RulesFile(Strict):
    rules: list[Rule]


# instrument_policy.yaml


class BondPairItem(Strict):
    country: str
    name: str
    isin: str
    maturity: date
    lot: Money | None = None


class BucketPolicy(Strict):
    allowed: list[str | dict[str, Any]] = []
    alternation_pair: list[BondPairItem] | None = None
    fallback: str | None = None
    under_review: list[str] = []


class InstrumentPolicyFile(Strict):
    buckets: dict[str, BucketPolicy]
    never_buy: list[str] = []


# The whole config


class AppConfig(Strict):
    settings: SettingsFile
    accounts: list[Account]
    categories: list[Category]
    buckets: list[Bucket]
    rules: list[Rule]
    instrument_policy: InstrumentPolicyFile
    plan: str

    @property
    def default_account(self) -> Account:
        return next(a for a in self.accounts if a.is_default)

    def bucket(self, bucket_id: str) -> Bucket:
        return next(b for b in self.buckets if b.id == bucket_id)
