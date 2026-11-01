import { fireEvent, screen, waitFor, within } from "@testing-library/react";

import { calls, lastCall, mockApi, renderPage, Reply, sent } from "@/test-utils";

import { MovimentiPage } from "./MovimentiPage";

const nbsp = (s: string | null) => (s ?? "").replace(/\s/g, " ");

function tx(id: number, over: Record<string, unknown> = {}) {
  return {
    id,
    date: "2026-03-14",
    amount: "12.50",
    from_account: "Banca Aurora",
    to_account: null,
    category: "🍝 Ristoranti",
    subcategory: "Pizzeria",
    note: `Nota ${id}`,
    tag: null,
    exclude_from_stats: false,
    direction: "expense",
    source: "manual",
    created_at: "2026-03-14T10:00:00Z",
    ...over,
  };
}

const PAGE = {
  items: [
    tx(1),
    tx(2, {
      amount: "2150.00",
      from_account: null,
      to_account: "Banca Aurora",
      category: "💰 Stipendio",
      subcategory: null,
      direction: "income",
    }),
    tx(3, {
      amount: "80.00",
      to_account: "Contanti",
      direction: "transfer",
      tag: "lisbona",
      exclude_from_stats: true,
    }),
  ],
  total: 3,
};

afterEach(() => vi.unstubAllGlobals());

function rows() {
  return screen.getAllByRole("row").slice(1); // skip the header row
}

it("shows rows with signed Italian amounts, accounts and categories", async () => {
  mockApi({ "/api/transactions": PAGE });
  renderPage(<MovimentiPage />, "/movimenti");

  await waitFor(() => expect(rows()).toHaveLength(3));
  const [expense, income, transfer] = rows() as [HTMLElement, HTMLElement, HTMLElement];
  expect(nbsp(expense.textContent)).toContain("14/03/2026");
  expect(nbsp(expense.textContent)).toContain("−12,50 €");
  expect(expense.textContent).toContain("Pizzeria");
  expect(nbsp(income.textContent)).toContain("+2.150,00 €");
  expect(nbsp(transfer.textContent)).toContain("80,00 €");
  expect(transfer.textContent).toContain("Banca Aurora → Contanti");
  expect(transfer.textContent).toContain("lisbona");
  expect(within(transfer).getByText("escluso")).toBeInTheDocument();
  expect(within(expense).queryByText("escluso")).toBeNull();
});

it("shows the empty state", async () => {
  mockApi({});
  renderPage(<MovimentiPage />, "/movimenti");
  expect(await screen.findByText("Nessun movimento trovato.")).toBeInTheDocument();
});

it("shows the error state", async () => {
  mockApi({ "/api/transactions": new Error("down") });
  renderPage(<MovimentiPage />, "/movimenti");
  expect(await screen.findByText("Impossibile caricare i movimenti.")).toBeInTheDocument();
});

it("applies filters from the URL on load", async () => {
  const fetchMock = mockApi({ "/api/transactions": PAGE });
  renderPage(<MovimentiPage />, "/movimenti?account=Contanti&q=pizza");

  await waitFor(() => expect(calls(fetchMock, "/api/transactions").length).toBeGreaterThan(0));
  const params = lastCall(fetchMock, "/api/transactions");
  expect(params.get("account")).toBe("Contanti");
  expect(params.get("q")).toBe("pizza");
  expect(await screen.findByLabelText("Conto")).toHaveValue("Contanti");
});

it("changing a filter updates the URL and the query, and resets the page", async () => {
  const fetchMock = mockApi({ "/api/transactions": PAGE });
  renderPage(<MovimentiPage />, "/movimenti?offset=50");

  const category = await screen.findByLabelText("Categoria");
  await screen.findByRole("option", { name: "💰 Stipendio" });
  fireEvent.change(category, { target: { value: "💰 Stipendio" } });
  fireEvent.change(screen.getByLabelText("Dal"), { target: { value: "2026-02-01" } });
  fireEvent.change(screen.getByLabelText("Tag"), { target: { value: "lisbona" } });

  await waitFor(() => {
    const params = lastCall(fetchMock, "/api/transactions");
    expect(params.get("category")).toBe("💰 Stipendio");
    expect(params.get("date_from")).toBe("2026-02-01");
    expect(params.get("tag")).toBe("lisbona");
    expect(params.get("offset")).toBe("0");
  });
  const location = screen.getByTestId("location").textContent ?? "";
  const search = new URLSearchParams(location.split("?")[1]);
  expect(search.get("category")).toBe("💰 Stipendio");
  expect(search.get("offset")).toBeNull();
});

it("text search is applied after typing stops", async () => {
  const fetchMock = mockApi({ "/api/transactions": PAGE });
  renderPage(<MovimentiPage />, "/movimenti");

  fireEvent.change(await screen.findByLabelText("Cerca"), { target: { value: "pizza" } });
  await waitFor(() =>
    expect(lastCall(fetchMock, "/api/transactions").get("q")).toBe("pizza"),
  );
});

it("paginates 50 rows at a time", async () => {
  const fetchMock = mockApi({
    "/api/transactions": (url: URL) => ({
      items: [tx(Number(url.searchParams.get("offset")) + 1)],
      total: 120,
    }),
  });
  renderPage(<MovimentiPage />, "/movimenti");

  expect(await screen.findByText("1–50 di 120")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Precedente" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Successivo" }));
  expect(await screen.findByText("51–100 di 120")).toBeInTheDocument();
  expect(lastCall(fetchMock, "/api/transactions").get("offset")).toBe("50");
  fireEvent.click(screen.getByRole("button", { name: "Successivo" }));
  expect(await screen.findByText("101–120 di 120")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Successivo" })).toBeDisabled();
});

describe("changing the ledger", () => {
  it("adds a line and reloads the table", async () => {
    let created = false;
    const fetchMock = mockApi({
      "GET /api/transactions": () => (created ? { items: [tx(7)], total: 1 } : { items: [], total: 0 }),
      "POST /api/transactions": () => {
        created = true;
        return new Reply(201, tx(7));
      },
    });
    renderPage(<MovimentiPage />, "/movimenti");

    fireEvent.click(await screen.findByRole("button", { name: "Aggiungi movimento" }));
    const form = within(await screen.findByRole("form"));
    await form.findByRole("option", { name: "🍝 Ristoranti" });
    fireEvent.change(form.getByLabelText("Importo"), { target: { value: "12,50" } });
    fireEvent.change(form.getByLabelText("Categoria"), { target: { value: "🍝 Ristoranti" } });
    fireEvent.click(form.getByRole("button", { name: "Salva" }));

    await waitFor(() => expect(sent(fetchMock, "POST", "/api/transactions")).toHaveLength(1));
    expect(sent(fetchMock, "POST", "/api/transactions")[0]?.[1]).toMatchObject({ amount: "12.50" });
    await waitFor(() => expect(rows()).toHaveLength(1));
    expect(screen.queryByRole("form")).toBeNull();
  });

  it("edits a row inline with a PATCH", async () => {
    const fetchMock = mockApi({
      "GET /api/transactions": PAGE,
      "PATCH /api/transactions": new Reply(200, tx(1, { amount: "20.00" })),
    });
    renderPage(<MovimentiPage />, "/movimenti");

    await waitFor(() => expect(rows()).toHaveLength(3));
    fireEvent.click(within(rows()[0] as HTMLElement).getByRole("button", { name: "Modifica" }));
    const form = within(await screen.findByRole("form"));
    expect(form.getByLabelText("Importo")).toHaveValue("12,50");
    fireEvent.change(form.getByLabelText("Importo"), { target: { value: "20" } });
    fireEvent.click(form.getByRole("button", { name: "Salva" }));

    await waitFor(() => expect(sent(fetchMock, "PATCH", "/api/transactions/1")).toHaveLength(1));
    expect(sent(fetchMock, "PATCH", "/api/transactions/1")[0]?.[1]).toMatchObject({ amount: "20.00" });
    await waitFor(() => expect(screen.queryByRole("form")).toBeNull());
  });

  it("deletes after confirmation, and cancelling sends nothing", async () => {
    const fetchMock = mockApi({
      "GET /api/transactions": PAGE,
      "DELETE /api/transactions": new Reply(204),
    });
    renderPage(<MovimentiPage />, "/movimenti");
    await waitFor(() => expect(rows()).toHaveLength(3));

    fireEvent.click(within(rows()[1] as HTMLElement).getByRole("button", { name: "Elimina" }));
    let dialog = within(await screen.findByRole("dialog"));
    expect(dialog.getByText("Eliminare questo movimento?")).toBeInTheDocument();
    fireEvent.click(dialog.getByRole("button", { name: "Annulla" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(sent(fetchMock, "DELETE", "/api/transactions")).toHaveLength(0);

    fireEvent.click(within(rows()[1] as HTMLElement).getByRole("button", { name: "Elimina" }));
    dialog = within(await screen.findByRole("dialog"));
    fireEvent.click(dialog.getByRole("button", { name: "Elimina" }));
    await waitFor(() => expect(sent(fetchMock, "DELETE", "/api/transactions/2")).toHaveLength(1));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(calls(fetchMock, "/api/transactions").length).toBeGreaterThan(1); // reloaded
  });

  it("explains why an adjustment line cannot be deleted", async () => {
    mockApi({
      "GET /api/transactions": PAGE,
      "DELETE /api/transactions": new Reply(409, {
        key: "error.linkedToBalanceCheck",
        field: null,
        message: "linked",
      }),
    });
    renderPage(<MovimentiPage />, "/movimenti");
    await waitFor(() => expect(rows()).toHaveLength(3));

    fireEvent.click(within(rows()[0] as HTMLElement).getByRole("button", { name: "Elimina" }));
    const dialog = within(await screen.findByRole("dialog"));
    fireEvent.click(dialog.getByRole("button", { name: "Elimina" }));
    expect(await dialog.findByText(/rettifica di una verifica saldo/)).toBeInTheDocument();
  });
});

it("export links download the filtered ledger", async () => {
  mockApi({ "/api/transactions": PAGE });
  renderPage(<MovimentiPage />, "/movimenti?account=Contanti&q=pizza&offset=50");

  const csvLink = await screen.findByRole("link", { name: "CSV" });
  const csvUrl = new URL(csvLink.getAttribute("href") ?? "", "http://localhost");
  expect(csvUrl.pathname).toBe("/api/transactions/export");
  expect(csvUrl.searchParams.get("format")).toBe("csv");
  expect(csvUrl.searchParams.get("account")).toBe("Contanti");
  expect(csvUrl.searchParams.get("q")).toBe("pizza");
  expect(csvUrl.searchParams.get("offset")).toBeNull();
  expect(csvLink).toHaveAttribute("download");

  const xlsx = new URL(
    screen.getByRole("link", { name: "Excel" }).getAttribute("href") ?? "",
    "http://localhost",
  );
  expect(xlsx.searchParams.get("format")).toBe("xlsx");
  expect(xlsx.searchParams.get("account")).toBe("Contanti");
});
