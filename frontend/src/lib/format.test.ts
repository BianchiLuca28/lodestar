import { formatDate, formatMoney } from "./format";

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
