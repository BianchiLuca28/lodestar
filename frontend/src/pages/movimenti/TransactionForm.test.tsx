import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";

import "@/i18n";
import { CONFIG } from "@/test-utils";

import { TransactionForm } from "./TransactionForm";
import { ApiError, type AppConfig, type Transaction } from "./useTransactions";

const config = CONFIG as AppConfig;

function setup(initial?: Transaction) {
  const onSubmit = vi.fn<(payload: unknown) => Promise<void>>().mockResolvedValue(undefined);
  const onCancel = vi.fn();
  render(
    <TransactionForm
      config={config}
      initial={initial}
      today="2026-11-05"
      onSubmit={onSubmit}
      onCancel={onCancel}
    />,
  );
  const form = within(screen.getByRole("form"));
  return { form, onSubmit, onCancel };
}

const change = (el: HTMLElement, value: string) => fireEvent.change(el, { target: { value } });

it("starts as an expense from the default account, dated today", () => {
  const { form } = setup();
  expect(form.getByRole("radio", { name: "Uscita" })).toBeChecked();
  expect(form.getByLabelText("Da")).toHaveValue("Banca Aurora");
  expect(form.queryByLabelText("Verso")).toBeNull();
  expect(form.getByLabelText("Data")).toHaveValue("2026-11-05");
});

it("the type decides which accounts are shown", () => {
  const { form } = setup();
  fireEvent.click(form.getByRole("radio", { name: "Entrata" }));
  expect(form.queryByLabelText("Da")).toBeNull();
  expect(form.getByLabelText("Verso")).toHaveValue("Banca Aurora");
  fireEvent.click(form.getByRole("radio", { name: "Trasferimento" }));
  expect(form.getByLabelText("Da")).toBeInTheDocument();
  expect(form.getByLabelText("Verso")).toBeInTheDocument();
});

it("subcategory is a list when the category has some, free text otherwise", () => {
  const { form } = setup();
  change(form.getByLabelText("Categoria"), "🍝 Ristoranti");
  expect(form.getByLabelText("Sottocategoria").tagName).toBe("SELECT");
  change(form.getByLabelText("Categoria"), "💰 Stipendio");
  expect(form.getByLabelText("Sottocategoria").tagName).toBe("INPUT");
});

it("submits an expense with the amount in API format", async () => {
  const { form, onSubmit } = setup();
  change(form.getByLabelText("Importo"), "12,5");
  change(form.getByLabelText("Categoria"), "🍝 Ristoranti");
  change(form.getByLabelText("Sottocategoria"), "Pizzeria");
  change(form.getByLabelText("Nota"), "Pizza");
  fireEvent.click(form.getByLabelText("Escludi dalle statistiche"));
  fireEvent.click(form.getByRole("button", { name: "Salva" }));

  await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
  expect(onSubmit).toHaveBeenCalledWith({
    date: "2026-11-05",
    amount: "12.50",
    from_account: "Banca Aurora",
    to_account: null,
    category: "🍝 Ristoranti",
    subcategory: "Pizzeria",
    note: "Pizza",
    tag: null,
    exclude_from_stats: true,
  });
});

it("a transfer sends both accounts", async () => {
  const { form, onSubmit } = setup();
  fireEvent.click(form.getByRole("radio", { name: "Trasferimento" }));
  change(form.getByLabelText("Verso"), "Contanti");
  change(form.getByLabelText("Importo"), "80");
  change(form.getByLabelText("Categoria"), "💰 Stipendio");
  fireEvent.click(form.getByRole("button", { name: "Salva" }));
  await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
  expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({
    from_account: "Banca Aurora",
    to_account: "Contanti",
    amount: "80.00",
  });
});

it("an unreadable amount is flagged without calling the API", async () => {
  const { form, onSubmit } = setup();
  change(form.getByLabelText("Importo"), "dodici");
  change(form.getByLabelText("Categoria"), "🍝 Ristoranti");
  fireEvent.click(form.getByRole("button", { name: "Salva" }));
  expect(await form.findByText(/Importo non valido/)).toBeInTheDocument();
  expect(onSubmit).not.toHaveBeenCalled();
});

it("shows an API validation error next to its field", async () => {
  const { form, onSubmit } = setup();
  onSubmit.mockRejectedValueOnce(new ApiError(422, "error.unknownCategory", "category", "x"));
  change(form.getByLabelText("Importo"), "5");
  change(form.getByLabelText("Categoria"), "🍝 Ristoranti");
  fireEvent.click(form.getByRole("button", { name: "Salva" }));
  const message = await form.findByText("Categoria sconosciuta.");
  expect(form.getByLabelText("Categoria")).toHaveAttribute("aria-describedby", message.id);
});

it("prefills when editing and keeps an income an income", async () => {
  const income: Transaction = {
    id: 9,
    date: "2026-10-27",
    amount: "2150.00",
    from_account: null,
    to_account: "Banca Aurora",
    category: "💰 Stipendio",
    subcategory: "Mensilità",
    note: "Stipendio",
    tag: null,
    exclude_from_stats: false,
    direction: "income",
    source: "import",
    created_at: "2026-11-01T10:00:00Z",
  };
  const { form, onSubmit, onCancel } = setup(income);
  expect(form.getByRole("radio", { name: "Entrata" })).toBeChecked();
  expect(form.getByLabelText("Importo")).toHaveValue("2150,00");
  expect(form.getByLabelText("Sottocategoria")).toHaveValue("Mensilità");
  fireEvent.click(form.getByRole("button", { name: "Salva" }));
  await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
  expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({ from_account: null, to_account: "Banca Aurora" });
  fireEvent.click(form.getByRole("button", { name: "Annulla" }));
  expect(onCancel).toHaveBeenCalled();
});
