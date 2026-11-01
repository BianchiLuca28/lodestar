import { fireEvent, screen, waitFor, within } from "@testing-library/react";

import { calls, mockApi, renderPage, Reply, sent } from "@/test-utils";

import { Balances } from "./Balances";

const nbsp = (s: string | null) => (s ?? "").replace(/\s/g, " ");

const BALANCES = [
  { account: "Banca Aurora", balance: "1317.50" },
  { account: "Contanti", balance: "-5.00" },
];

const CHECK = {
  id: 1,
  account: "Banca Aurora",
  date: "2026-03-10",
  real_balance: "1300.00",
  computed_balance: "1330.00",
  gap: "-30.00",
  adjustment: null,
};

afterEach(() => vi.unstubAllGlobals());

function card(account: string) {
  return within(screen.getByRole("listitem", { name: account }));
}

it("shows each account's computed balance in Italian format", async () => {
  mockApi({ "/api/accounts/balances": BALANCES, "/api/balance-checks": [] });
  renderPage(<Balances />, "/movimenti");

  await screen.findByRole("listitem", { name: "Banca Aurora" });
  expect(nbsp(card("Banca Aurora").getByText(/€/).textContent)).toBe("1.317,50 €");
  expect(nbsp(card("Contanti").getByText(/€/).textContent)).toBe("-5,00 €");
});

it("shows the last check under its account", async () => {
  mockApi({ "/api/accounts/balances": BALANCES, "/api/balance-checks": [CHECK] });
  renderPage(<Balances />, "/movimenti");

  await screen.findByRole("listitem", { name: "Banca Aurora" });
  const text = nbsp(card("Banca Aurora").getByText(/Ultima verifica/).textContent);
  expect(text).toContain("10/03/2026");
  expect(text).toContain("-30,00 €");
  expect(card("Contanti").queryByText(/Ultima verifica/)).toBeNull();
});

it("previews the gap, then confirms and reloads", async () => {
  const fetchMock = mockApi({
    "/api/accounts/balances": BALANCES,
    "GET /api/balance-checks": [],
    "POST /api/balance-checks/preview": { computed: "1330.00", gap: "-30.00" },
    "POST /api/balance-checks": new Reply(201, CHECK),
  });
  renderPage(<Balances />, "/movimenti");

  await screen.findByRole("listitem", { name: "Banca Aurora" });
  fireEvent.click(card("Banca Aurora").getByRole("button", { name: "Verifica saldo" }));
  const dialog = within(await screen.findByRole("dialog"));
  fireEvent.change(dialog.getByLabelText("Data"), { target: { value: "2026-03-10" } });
  fireEvent.change(dialog.getByLabelText("Saldo reale"), { target: { value: "1.300,00" } });
  fireEvent.click(dialog.getByRole("button", { name: "Calcola differenza" }));

  const gap = await dialog.findByText(/Differenza/);
  expect(nbsp(gap.textContent)).toContain("-30,00 €");
  expect(sent(fetchMock, "POST", "/api/balance-checks/preview")[0]?.[1]).toEqual({
    account: "Banca Aurora",
    date: "2026-03-10",
    real_balance: "1300.00",
  });

  const before = calls(fetchMock, "/api/accounts/balances").length;
  fireEvent.click(dialog.getByRole("button", { name: "Conferma" }));
  await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  const posts = sent(fetchMock, "POST", "/api/balance-checks").filter(
    ([url]) => url.pathname === "/api/balance-checks",
  );
  expect(posts).toHaveLength(1);
  await waitFor(() =>
    expect(calls(fetchMock, "/api/accounts/balances").length).toBeGreaterThan(before),
  );
});

it("says when the balance is already right", async () => {
  mockApi({
    "/api/accounts/balances": BALANCES,
    "GET /api/balance-checks": [],
    "POST /api/balance-checks/preview": { computed: "1317.50", gap: "0.00" },
  });
  renderPage(<Balances />, "/movimenti");

  await screen.findByRole("listitem", { name: "Banca Aurora" });
  fireEvent.click(card("Banca Aurora").getByRole("button", { name: "Verifica saldo" }));
  const dialog = within(await screen.findByRole("dialog"));
  fireEvent.change(dialog.getByLabelText("Saldo reale"), { target: { value: "1317,50" } });
  fireEvent.click(dialog.getByRole("button", { name: "Calcola differenza" }));
  expect(await dialog.findByText("Saldo corretto: nessuna rettifica necessaria.")).toBeInTheDocument();
});

it("flags an unreadable balance without calling the API", async () => {
  const fetchMock = mockApi({ "/api/accounts/balances": BALANCES, "/api/balance-checks": [] });
  renderPage(<Balances />, "/movimenti");

  await screen.findByRole("listitem", { name: "Banca Aurora" });
  fireEvent.click(card("Banca Aurora").getByRole("button", { name: "Verifica saldo" }));
  const dialog = within(await screen.findByRole("dialog"));
  fireEvent.change(dialog.getByLabelText("Saldo reale"), { target: { value: "tanti" } });
  fireEvent.click(dialog.getByRole("button", { name: "Calcola differenza" }));
  expect(await dialog.findByText(/Importo non valido/)).toBeInTheDocument();
  expect(sent(fetchMock, "POST", "/api/balance-checks")).toHaveLength(0);
});
