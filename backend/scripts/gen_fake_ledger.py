"""Generate the fake persona's ledger: config.example/ledger.csv.

Deterministic: the same seed always produces a byte-identical file.
Usage: uv run python scripts/gen_fake_ledger.py [--seed N]
"""

import argparse
import csv
import io
import random
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "config.example" / "ledger.csv"
DEFAULT_SEED = 2026
MONTHS = range(1, 11)  # January to October 2026
YEAR = 2026
TRIP_TAG = "vacanza-lisbona-2026"

HEADER = [
    "date",
    "amount",
    "from_account",
    "to_account",
    "category",
    "subcategory",
    "note",
    "tag",
    "exclude_from_stats",
]

BANK = "Banca Aurora"
CASH = "Contanti"
CARD = "Carta Nebbia"
BROKER = "Broker Orsa"

SPESA = "🥦 Spesa"
RISTORANTI = "🍝 Ristoranti"
BOLLETTE = "💡 Bollette"
TRASPORTI = "🚲 Trasporti"
SVAGO = "🎬 Svago"
SHOPPING = "🛍️ Shopping"
ABBONAMENTI = "📺 Abbonamenti"
VACANZE = "🧳 Vacanze"
SALUTE = "🩺 Salute"
REGALI = "🎁 Regali"
VARIE = "❓ Varie"


@dataclass(frozen=True)
class Row:
    day: date
    cents: int
    from_account: str
    to_account: str
    category: str
    subcategory: str
    note: str
    tag: str = ""
    excluded: bool = False

    def as_list(self) -> list[str]:
        amount = Decimal(self.cents) / 100
        return [
            self.day.isoformat(),
            f"{amount:.2f}",
            self.from_account,
            self.to_account,
            self.category,
            self.subcategory,
            self.note,
            self.tag,
            "true" if self.excluded else "false",
        ]


def expense(
    d: date,
    cents: int,
    account: str,
    cat: str,
    sub: str,
    note: str,
    tag: str = "",
    excluded: bool = False,
) -> Row:
    return Row(d, cents, account, "", cat, sub, note, tag, excluded)


def monthly(rng: random.Random, m: int) -> list[Row]:
    d = lambda day: date(YEAR, m, day)  # noqa: E731
    pay = lambda: rng.choice([BANK, BANK, CARD, CASH])  # noqa: E731
    rows = [
        Row(d(27), 215000, "", BANK, "💰 Stipendio", "Mensilità", "Stipendio"),
        expense(d(1), 60000, BANK, "🏡 Affitto", "Canone", "Affitto via Saragozza"),
        Row(d(2), 65000, BANK, BROKER, "📊 Investimenti", "ETF", "Bonifico mensile al broker"),
        Row(d(10), 20000, BANK, CARD, VARIE, "", "Ricarica carta"),
        Row(d(rng.randint(5, 20)), 15000, BANK, CASH, VARIE, "", "Prelievo bancomat"),
        expense(
            d(rng.randint(3, 8)), rng.randint(3500, 7500), BANK, BOLLETTE, "Luce", "Bolletta luce"
        ),
        expense(
            d(rng.randint(3, 8)), rng.randint(2000, 9000), BANK, BOLLETTE, "Gas", "Bolletta gas"
        ),
        expense(d(12), 2799, BANK, BOLLETTE, "Internet", "Fibra casa"),
        expense(d(15), 999, BANK, BOLLETTE, "Telefono", "Ricarica telefono"),
        expense(d(4), 1299, CARD, ABBONAMENTI, "Streaming", "Abbonamento streaming"),
        expense(d(5), 3900, BANK, ABBONAMENTI, "Palestra", "Palestra di quartiere"),
    ]
    shops = ["Coop", "Conad", "Esselunga", "Mercato delle Erbe", "Forno Bianchi"]
    for _ in range(8):
        shop = rng.choice(shops)
        sub = "Mercato" if "Mercato" in shop else "Panificio" if "Forno" in shop else "Supermercato"
        rows.append(expense(d(rng.randint(1, 28)), rng.randint(800, 6500), pay(), SPESA, sub, shop))
    places = [
        ("Trattoria", "Trattoria da Nino"),
        ("Pizzeria", "Pizzeria La Lanterna"),
        ("Aperitivo", "Spritz con le colleghe"),
        ("Caffè", "Colazione al bar"),
    ]
    for _ in range(5):
        sub, note = rng.choice(places)
        lo, hi = (250, 900) if sub == "Caffè" else (1200, 4500)
        rows.append(
            expense(d(rng.randint(1, 28)), rng.randint(lo, hi), pay(), RISTORANTI, sub, note)
        )
    for _ in range(2):
        sub, note, cents = rng.choice(
            [("Treno", "Treno per Modena", 590), ("Bici", "Camera d'aria bici", 850)]
        )
        rows.append(expense(d(rng.randint(1, 28)), cents, pay(), TRASPORTI, sub, note))
    fun = [("Cinema", "Cinema Lumière", 800), ("Libri", "Libreria Coop", 1800)]
    fun += [("Concerti", "Concerto all'Estragon", 2500), ("Giochi", "Gioco da tavolo", 3400)]
    for _ in range(2):
        sub, note, cents = rng.choice(fun)
        rows.append(expense(d(rng.randint(1, 28)), cents, pay(), SVAGO, sub, note))
    if m % 2 == 0:
        sub, note = rng.choice([("Vestiti", "Maglione"), ("Scarpe", "Scarpe da corsa")])
        rows.append(
            expense(d(rng.randint(1, 28)), rng.randint(2500, 8000), BANK, SHOPPING, sub, note)
        )
    if m % 3 == 1:
        rows.append(
            expense(
                d(rng.randint(1, 28)), rng.randint(600, 2500), CARD, SALUTE, "Farmacia", "Farmacia"
            )
        )
    return rows


def one_offs() -> list[Row]:
    t = TRIP_TAG
    return [
        # Trip to Lisbon
        expense(date(YEAR, 5, 3), 18900, BANK, VACANZE, "Viaggio", "Volo Bologna-Lisbona", tag=t),
        expense(
            date(YEAR, 6, 12),
            34000,
            BANK,
            VACANZE,
            "Alloggio",
            "Appartamento Alfama, 4 notti",
            tag=t,
        ),
        expense(
            date(YEAR, 6, 12), 2350, CARD, RISTORANTI, "Trattoria", "Cena a Bairro Alto", tag=t
        ),
        expense(date(YEAR, 6, 13), 1500, CASH, VACANZE, "Attività", "Tram 28 e funicolare", tag=t),
        expense(date(YEAR, 6, 13), 1890, CARD, RISTORANTI, "Caffè", "Pastéis de nata", tag=t),
        expense(date(YEAR, 6, 14), 2400, CARD, VACANZE, "Attività", "Museo degli azulejos", tag=t),
        expense(date(YEAR, 6, 15), 4120, CARD, RISTORANTI, "Trattoria", "Cena di pesce", tag=t),
        # Refunds: income in the expense's category
        Row(
            date(YEAR, 6, 20),
            17000,
            "",
            BANK,
            VACANZE,
            "Alloggio",
            "Chiara mi ha ridato la sua metà dell'alloggio",
            tag=t,
        ),
        expense(
            date(YEAR, 3, 14), 9600, BANK, RISTORANTI, "Pizzeria", "Pizza per quattro, offro io"
        ),
        Row(
            date(YEAR, 3, 15),
            7200,
            "",
            BANK,
            RISTORANTI,
            "Pizzeria",
            "Rimborso pizza da Paolo, Sara e Teo",
        ),
        expense(date(YEAR, 8, 2), 5900, BANK, SHOPPING, "Scarpe", "Scarpe sbagliate"),
        Row(date(YEAR, 8, 9), 5900, "", BANK, SHOPPING, "Scarpe", "Reso scarpe"),
        Row(
            date(YEAR, 9, 18), 1250, "", BANK, SVAGO, "Concerti", "Giulia mi ha ridato il biglietto"
        ),
        # Gifts and a couple of extras
        expense(date(YEAR, 4, 22), 4500, BANK, REGALI, "Compleanni", "Regalo compleanno mamma"),
        expense(date(YEAR, 9, 5), 13900, BANK, SALUTE, "Visite", "Visita dentistica"),
        # Excluded from stats: money passing through for others, and a cash adjustment
        expense(
            date(YEAR, 7, 7),
            12000,
            BANK,
            SVAGO,
            "Concerti",
            "Biglietti concerto per il gruppo",
            excluded=True,
        ),
        Row(
            date(YEAR, 7, 10),
            12000,
            "",
            BANK,
            SVAGO,
            "Concerti",
            "Il gruppo mi ha ridato i biglietti",
            excluded=True,
        ),
        expense(
            date(YEAR, 10, 31),
            1340,
            CASH,
            VARIE,
            "",
            "Riallineamento saldo contanti",
            excluded=True,
        ),
    ]


def generate(seed: int = DEFAULT_SEED) -> str:
    rng = random.Random(seed)
    rows = [r for m in MONTHS for r in monthly(rng, m)] + one_offs()
    rows.sort(key=lambda r: r.day)  # stable: same-day rows keep generation order
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(r.as_list() for r in rows)
    return buf.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    OUTPUT.write_bytes(generate(args.seed).encode("utf-8"))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
