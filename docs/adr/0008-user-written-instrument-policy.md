# Investment suggestions come only from a user-written instrument policy

Status: the net-yield ranking is superseded by ADR-0016; the user-written policy and the ban on inferred preferences still hold.

When a bucket needs a purchase, the agent ranks candidates (by net yield to maturity for bonds) only within instrument_policy.yaml: allowed asset classes per bucket, maturity window, preferences and blacklist, all written by the user. Preferences are never inferred from history, and nothing is ever suggested because of price movements: the user is a passive, long-term investor.

## Considered Options

- Infer preferences from past trades: the history holds a single trade, and inferred preferences would be opaque.
