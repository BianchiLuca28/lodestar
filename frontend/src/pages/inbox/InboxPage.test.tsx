import { fireEvent, screen, waitFor, within } from "@testing-library/react";

import { Nav } from "@/components/Nav";
import { mockApi, renderPage, sent } from "@/test-utils";

import { InboxPage } from "./InboxPage";

const nbsp = (s: string | null) => (s ?? "").replace(/\s/g, " ");

function line(over: Record<string, unknown> = {}) {
  return {
    date: "2026-03-14",
    amount: "50.00",
    from_account: "Banca Aurora",
    to_account: null,
    category: "🍝 Ristoranti",
    subcategory: "Pizzeria",
    note: "Cena",
    tag: null,
    exclude_from_stats: false,
    possible_duplicates: [],
    ...over,
  };
}

function draft(id: number, lines = [line()], over: Record<string, unknown> = {}) {
  return {
    id,
    status: "pending",
    version: 1,
    source: "telegram",
    origin_text: `Messaggio ${id}`,
    confidence: null,
    created_at: "2026-03-14T19:30:00Z",
    decided_at: null,
    lines,
    ...over,
  };
}

const TWO = [
  draft(1, [line(), line({ amount: "25.00", from_account: null, to_account: "Banca Aurora", note: "Rimborso" })]),
  draft(2, [line({ amount: "12.00", possible_duplicates: [7] })]),
];

afterEach(() => vi.unstubAllGlobals());

function cards() {
  return screen.getAllByRole("article");
}

it("shows each draft with its message, Italian amounts and the duplicate badge", async () => {
  mockApi({ "/api/drafts": TWO });
  renderPage(<InboxPage />, "/inbox");

  await waitFor(() => expect(cards()).toHaveLength(2));
  const [first, second] = cards() as [HTMLElement, HTMLElement];
  expect(first.textContent).toContain("Messaggio 1");
  expect(nbsp(first.textContent)).toContain("−50,00 €");
  expect(nbsp(first.textContent)).toContain("+25,00 €");
  expect(within(first).queryByText("Possibile duplicato")).toBeNull();
  expect(within(second).getByText("Possibile duplicato")).toBeInTheDocument();
});

it("approves and rejects a draft", async () => {
  const api = mockApi({ "/api/drafts": TWO, "POST /api/drafts": draft(1, [line()], { status: "approved" }) });
  renderPage(<InboxPage />, "/inbox");

  await waitFor(() => expect(cards()).toHaveLength(2));
  const [first, second] = cards() as [HTMLElement, HTMLElement];
  fireEvent.click(within(first).getByRole("button", { name: "Approva" }));
  fireEvent.click(within(second).getByRole("button", { name: "Rifiuta" }));
  await waitFor(() => expect(sent(api, "POST", "/api/drafts")).toHaveLength(2));
  const paths = sent(api, "POST", "/api/drafts").map(([url]) => url.pathname);
  expect(paths).toEqual(["/api/drafts/1/approve", "/api/drafts/2/reject"]);
});

it("editing one line sends every line with that one replaced", async () => {
  const api = mockApi({ "/api/drafts": TWO, "PUT /api/drafts": draft(1) });
  renderPage(<InboxPage />, "/inbox");

  await waitFor(() => expect(cards()).toHaveLength(2));
  const first = cards()[0] as HTMLElement;
  fireEvent.click(within(first).getAllByRole("button", { name: "Modifica riga" })[0] as HTMLElement);
  const amount = within(first).getByLabelText("Importo");
  fireEvent.change(amount, { target: { value: "48,00" } });
  fireEvent.click(within(first).getByRole("button", { name: "Salva" }));

  await waitFor(() => expect(sent(api, "PUT", "/api/drafts/1/lines")).toHaveLength(1));
  const body = sent(api, "PUT", "/api/drafts/1/lines")[0]?.[1] as { lines: { amount: string; note: string }[] };
  expect(body.lines.map((l) => l.amount)).toEqual(["48.00", "25.00"]);
  expect(body.lines[1]?.note).toBe("Rimborso");
});

it("approve all skips possible duplicates", async () => {
  const api = mockApi({ "/api/drafts": TWO, "POST /api/drafts": draft(1, [line()], { status: "approved" }) });
  renderPage(<InboxPage />, "/inbox");

  fireEvent.click(await screen.findByRole("button", { name: "Approva tutte (1)" }));
  await waitFor(() => expect(sent(api, "POST", "/api/drafts")).toHaveLength(1));
  expect(sent(api, "POST", "/api/drafts")[0]?.[0].pathname).toBe("/api/drafts/1/approve");
  expect(await screen.findByText(/1 bozza con possibile duplicato da controllare/)).toBeInTheDocument();
});

it("shows the empty state", async () => {
  mockApi({ "/api/drafts": [] });
  renderPage(<InboxPage />, "/inbox");
  expect(await screen.findByText("Nessuna bozza da controllare.")).toBeInTheDocument();
});

it("shows the pending count in the nav", async () => {
  mockApi({ "/api/drafts": TWO });
  renderPage(<Nav />, "/");
  const link = await screen.findByRole("link", { name: /Inbox/ });
  await waitFor(() => expect(link.textContent).toContain("2"));
});
