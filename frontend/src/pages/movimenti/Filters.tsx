import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";

import type { AppConfig } from "./useTransactions";

export type FilterKey = "date_from" | "date_to" | "account" | "category" | "tag" | "q";
export type FilterValues = Partial<Record<FilterKey, string>>;

const TYPING_DELAY_MS = 300;

const field = "flex flex-col gap-1 text-xs text-gray-600";
const control = "rounded border border-gray-300 px-2 py-1 text-sm text-gray-900";

/** A text input that reports its value after typing pauses. Re-keyed when the value changes outside. */
function DebouncedInput({
  label,
  value,
  onCommit,
}: {
  label: string;
  value: string;
  onCommit: (value: string) => void;
}) {
  const id = useId();
  const [draft, setDraft] = useState(value);
  useEffect(() => {
    if (draft === value) return;
    const timer = setTimeout(() => onCommit(draft), TYPING_DELAY_MS);
    return () => clearTimeout(timer);
  }, [draft, value, onCommit]);
  return (
    <label htmlFor={id} className={field}>
      {label}
      <input
        id={id}
        type="search"
        className={control}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
      />
    </label>
  );
}

export function Filters({
  values,
  config,
  onChange,
  onClear,
}: {
  values: FilterValues;
  config: AppConfig | undefined;
  onChange: (key: FilterKey, value: string) => void;
  onClear: () => void;
}) {
  const { t } = useTranslation();
  const ids = { from: useId(), to: useId(), account: useId(), category: useId() };

  return (
    <div className="mb-4 flex flex-wrap items-end gap-3">
      <label htmlFor={ids.from} className={field}>
        {t("movimenti.filters.dateFrom")}
        <input
          id={ids.from}
          type="date"
          className={control}
          value={values.date_from ?? ""}
          onChange={(e) => onChange("date_from", e.target.value)}
        />
      </label>
      <label htmlFor={ids.to} className={field}>
        {t("movimenti.filters.dateTo")}
        <input
          id={ids.to}
          type="date"
          className={control}
          value={values.date_to ?? ""}
          onChange={(e) => onChange("date_to", e.target.value)}
        />
      </label>
      <label htmlFor={ids.account} className={field}>
        {t("movimenti.filters.account")}
        <select
          id={ids.account}
          className={control}
          value={values.account ?? ""}
          onChange={(e) => onChange("account", e.target.value)}
        >
          <option value="">{t("movimenti.filters.any")}</option>
          {config?.accounts.map((a) => (
            <option key={a.name} value={a.name}>
              {a.name}
            </option>
          ))}
        </select>
      </label>
      <label htmlFor={ids.category} className={field}>
        {t("movimenti.filters.category")}
        <select
          id={ids.category}
          className={control}
          value={values.category ?? ""}
          onChange={(e) => onChange("category", e.target.value)}
        >
          <option value="">{t("movimenti.filters.any")}</option>
          {config?.categories.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      <DebouncedInput
        key={`tag:${values.tag ?? ""}`}
        label={t("movimenti.filters.tag")}
        value={values.tag ?? ""}
        onCommit={(v) => onChange("tag", v)}
      />
      <DebouncedInput
        key={`q:${values.q ?? ""}`}
        label={t("movimenti.filters.search")}
        value={values.q ?? ""}
        onCommit={(v) => onChange("q", v)}
      />
      <button type="button" className="text-sm text-blue-700 underline" onClick={onClear}>
        {t("movimenti.filters.clear")}
      </button>
    </div>
  );
}
