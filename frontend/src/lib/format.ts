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
