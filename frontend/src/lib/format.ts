const money = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  useGrouping: "always",
});

/** Formats a decimal string from the API (e.g. "1234.56") as Italian euros. */
export function formatMoney(amount: string): string {
  return money.format(Number(amount));
}

/** Formats an ISO date (yyyy-MM-dd) as dd/MM/yyyy without timezone shifts. */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

export type Direction = "expense" | "income" | "transfer";

/** Money with a sign from the direction: −expense, +income, unsigned transfer. */
export function formatSignedMoney(amount: string, direction: Direction): string {
  const value = formatMoney(amount);
  if (direction === "expense") return `−${value}`;
  if (direction === "income") return `+${value}`;
  return value;
}

/**
 * Reads an amount typed the Italian way ("1.234,56", "12,5") or with a dot ("12.5"),
 * and returns it in API format with two decimals ("1234.56"), or null if unreadable.
 */
export function parseAmount(input: string): string | null {
  let text = input.trim();
  if (text.includes(",")) text = text.replace(/\./g, "").replace(",", ".");
  if (!/^\d+(\.\d{1,2})?$/.test(text)) return null;
  const [units, cents = ""] = text.split(".");
  return `${String(Number(units))}.${cents.padEnd(2, "0")}`;
}

/** An API amount ("12.50") as the user would type it ("12,50"). */
export function amountForInput(amount: string): string {
  return amount.replace(".", ",");
}

const romeDay = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Europe/Rome",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

/** Today's date in Rome as yyyy-MM-dd. */
export function todayRome(now: Date = new Date()): string {
  return romeDay.format(now);
}
