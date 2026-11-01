import { formatDate, formatMoney, formatSignedMoney } from "./format";

describe("formatSignedMoney", () => {
  const plain = (s: string) => s.replace(/\s/g, " ");
  it("signs expenses with a minus", () => {
    expect(plain(formatSignedMoney("12.5", "expense"))).toBe("−12,50 €");
  });
  it("signs incomes with a plus", () => {
    expect(plain(formatSignedMoney("2150", "income"))).toBe("+2.150,00 €");
  });
  it("leaves transfers unsigned", () => {
    expect(plain(formatSignedMoney("80", "transfer"))).toBe("80,00 €");
  });
});

describe("formatMoney", () => {
  it("formats euros the Italian way", () => {
    expect(formatMoney("1234.56").replace(/\s/g, " ")).toBe("1.234,56 €");
  });

  it("keeps two decimals", () => {
    expect(formatMoney("7").replace(/\s/g, " ")).toBe("7,00 €");
  });
});

describe("formatDate", () => {
  it("formats an ISO date as dd/MM/yyyy", () => {
    expect(formatDate("2026-11-01")).toBe("01/11/2026");
  });
});
