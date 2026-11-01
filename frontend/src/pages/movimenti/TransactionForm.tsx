import { type FormEvent, type ReactNode, useId, useState } from "react";
import { useTranslation } from "react-i18next";

import { amountForInput, parseAmount } from "@/lib/format";
import { cn } from "@/lib/utils";

import {
  ApiError,
  type AppConfig,
  type Transaction,
  type TransactionInput,
} from "./useTransactions";

type Kind = "expense" | "income" | "transfer";
type FieldName = "date" | "amount" | "from_account" | "to_account" | "category" | "subcategory";
type FormError = { field: FieldName | null; key: string };

const KINDS: Kind[] = ["expense", "income", "transfer"];
const control = "rounded border border-gray-300 px-2 py-1 text-sm";

function defaultAccount(config: AppConfig): string {
  return (config.accounts.find((a) => a.is_default) ?? config.accounts[0])?.name ?? "";
}

function otherAccount(config: AppConfig, not: string): string {
  return config.accounts.find((a) => a.name !== not)?.name ?? "";
}

export function TransactionForm({
  config,
  initial,
  today,
  onSubmit,
  onCancel,
}: {
  config: AppConfig;
  initial?: Transaction;
  today: string;
  onSubmit: (input: TransactionInput) => Promise<unknown>;
  onCancel: () => void;
}) {
  const { t } = useTranslation();
  const ids = useId();
  const fallback = defaultAccount(config);

  const [kind, setKind] = useState<Kind>(initial?.direction ?? "expense");
  const [date, setDate] = useState(initial?.date ?? today);
  const [amount, setAmount] = useState(initial ? amountForInput(initial.amount) : "");
  const [from, setFrom] = useState(initial?.from_account ?? fallback);
  const [to, setTo] = useState(
    initial?.to_account ?? (initial ? fallback : otherAccount(config, fallback)),
  );
  const [category, setCategory] = useState(initial?.category ?? "");
  const [subcategory, setSubcategory] = useState(initial?.subcategory ?? "");
  const [note, setNote] = useState(initial?.note ?? "");
  const [tag, setTag] = useState(initial?.tag ?? "");
  const [exclude, setExclude] = useState(initial?.exclude_from_stats ?? false);
  const [error, setError] = useState<FormError | null>(null);
  const [saving, setSaving] = useState(false);

  const subcategories = config.categories.find((c) => c.name === category)?.subcategories ?? [];
  const errorId = (field: FieldName) => `${ids}-${field}-error`;

  function chooseKind(next: Kind) {
    setKind(next);
    // Keep the accounts sensible: an income lands on the default account unless one is set.
    if (next === "income" && !to) setTo(fallback);
    if (next === "income" && kind === "expense") setTo(from || fallback);
    if (next === "expense" && kind === "income") setFrom(to || fallback);
    if (next === "transfer" && (!to || to === from)) setTo(otherAccount(config, from));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const parsed = parseAmount(amount);
    if (parsed === null) {
      setError({ field: "amount", key: "error.invalidAmount" });
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await onSubmit({
        date,
        amount: parsed,
        from_account: kind === "income" ? null : from || null,
        to_account: kind === "expense" ? null : to || null,
        category,
        subcategory: subcategory || null,
        note: note || null,
        tag: tag || null,
        exclude_from_stats: exclude,
      });
    } catch (err) {
      if (err instanceof ApiError) setError({ field: err.field as FieldName | null, key: err.key });
      else setError({ field: null, key: "movimenti.form.genericError" });
    } finally {
      setSaving(false);
    }
  }

  function Field({
    name,
    label,
    children,
  }: {
    name: FieldName | "note" | "tag";
    label: string;
    children: (props: { id: string; "aria-describedby"?: string }) => ReactNode;
  }) {
    const id = `${ids}-${name}`;
    const hasError = error?.field === name;
    return (
      <div className="flex flex-col gap-1 text-xs text-gray-600">
        <label htmlFor={id}>{label}</label>
        {children({ id, "aria-describedby": hasError ? errorId(name as FieldName) : undefined })}
        {hasError && (
          <span id={errorId(name as FieldName)} className="text-red-700">
            {t(error.key)}
          </span>
        )}
      </div>
    );
  }

  const accountOptions = config.accounts.map((a) => (
    <option key={a.name} value={a.name}>
      {a.name}
    </option>
  ));

  return (
    <form
      aria-label={t("movimenti.formLabel")}
      onSubmit={(e) => void submit(e)}
      className="mb-4 rounded border border-gray-200 bg-gray-50 p-4"
    >
      {error?.field === null && <p className="mb-3 text-sm text-red-700">{t(error.key)}</p>}

      <fieldset className="mb-3 flex gap-4 text-sm">
        <legend className="sr-only">{t("movimenti.form.type")}</legend>
        {KINDS.map((k) => (
          <label key={k} className="flex items-center gap-1">
            <input
              type="radio"
              name={`${ids}-kind`}
              checked={kind === k}
              onChange={() => chooseKind(k)}
            />
            {t(`movimenti.form.${k}`)}
          </label>
        ))}
      </fieldset>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {Field({
          name: "date",
          label: t("movimenti.form.date"),
          children: (p) => (
            <input {...p} type="date" className={control} value={date} onChange={(e) => setDate(e.target.value)} />
          ),
        })}
        {Field({
          name: "amount",
          label: t("movimenti.form.amount"),
          children: (p) => (
            <input
              {...p}
              inputMode="decimal"
              className={control}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          ),
        })}
        {kind !== "income" &&
          Field({
            name: "from_account",
            label: t("movimenti.form.from"),
            children: (p) => (
              <select {...p} className={control} value={from} onChange={(e) => setFrom(e.target.value)}>
                {accountOptions}
              </select>
            ),
          })}
        {kind !== "expense" &&
          Field({
            name: "to_account",
            label: t("movimenti.form.to"),
            children: (p) => (
              <select {...p} className={control} value={to} onChange={(e) => setTo(e.target.value)}>
                {accountOptions}
              </select>
            ),
          })}
        {Field({
          name: "category",
          label: t("movimenti.form.category"),
          children: (p) => (
            <select
              {...p}
              className={control}
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setSubcategory("");
              }}
            >
              <option value="">{t("movimenti.form.choose")}</option>
              {config.categories.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          ),
        })}
        {Field({
          name: "subcategory",
          label: t("movimenti.form.subcategory"),
          children: (p) =>
            subcategories.length > 0 ? (
              <select
                {...p}
                className={control}
                value={subcategory}
                onChange={(e) => setSubcategory(e.target.value)}
              >
                <option value="">{t("movimenti.form.none")}</option>
                {subcategories.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            ) : (
              <input
                {...p}
                className={control}
                value={subcategory}
                onChange={(e) => setSubcategory(e.target.value)}
              />
            ),
        })}
        {Field({
          name: "note",
          label: t("movimenti.form.note"),
          children: (p) => (
            <input {...p} className={control} value={note} onChange={(e) => setNote(e.target.value)} />
          ),
        })}
        {Field({
          name: "tag",
          label: t("movimenti.form.tag"),
          children: (p) => (
            <input {...p} className={control} value={tag} onChange={(e) => setTag(e.target.value)} />
          ),
        })}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={exclude} onChange={(e) => setExclude(e.target.checked)} />
          {t("movimenti.form.exclude")}
        </label>
        <div className="flex gap-2">
          <button type="button" className="rounded border px-3 py-1 text-sm" onClick={onCancel}>
            {t("movimenti.cancel")}
          </button>
          <button
            type="submit"
            disabled={saving}
            className={cn("rounded bg-blue-700 px-3 py-1 text-sm text-white", saving && "opacity-50")}
          >
            {t("movimenti.save")}
          </button>
        </div>
      </div>
    </form>
  );
}
