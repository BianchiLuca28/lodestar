import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { type FilterKey, Filters, type FilterValues } from "./Filters";
import { TransactionsTable } from "./TransactionsTable";
import { PAGE_SIZE, useConfig, useTransactions } from "./useTransactions";

const FILTER_KEYS: FilterKey[] = ["date_from", "date_to", "account", "category", "tag", "q"];

export function MovimentiPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useSearchParams();

  const filters: FilterValues = Object.fromEntries(
    FILTER_KEYS.flatMap((key) => {
      const value = search.get(key);
      return value ? [[key, value]] : [];
    }),
  );
  const offset = Math.max(0, Number(search.get("offset") ?? 0) || 0);

  const config = useConfig();
  const page = useTransactions({ ...filters, limit: PAGE_SIZE, offset });

  const setFilter = useCallback(
    (key: FilterKey, value: string) =>
      setSearch((prev) => {
        const next = new URLSearchParams(prev);
        if (value) next.set(key, value);
        else next.delete(key);
        next.delete("offset"); // a new filter starts from the first page
        return next;
      }),
    [setSearch],
  );
  const setOffset = (value: number) =>
    setSearch((prev) => {
      const next = new URLSearchParams(prev);
      if (value > 0) next.set("offset", String(value));
      else next.delete("offset");
      return next;
    });

  const total = page.data?.total ?? 0;
  const items = page.data?.items ?? [];

  return (
    <section>
      <h1 className="mb-4 text-2xl font-semibold">{t("nav.movimenti")}</h1>
      <Filters
        values={filters}
        config={config.data}
        onChange={setFilter}
        onClear={() => setSearch(new URLSearchParams())}
      />

      {page.isError && <p className="text-red-700">{t("movimenti.error")}</p>}
      {page.isPending && <p className="text-gray-500">{t("movimenti.loading")}</p>}
      {page.isSuccess && items.length === 0 && (
        <p className="text-gray-500">{t("movimenti.empty")}</p>
      )}
      {items.length > 0 && <TransactionsTable rows={items} />}

      {total > 0 && (
        <div className="mt-4 flex items-center justify-end gap-3 text-sm">
          <span>
            {t("movimenti.range", {
              from: offset + 1,
              to: Math.min(offset + PAGE_SIZE, total),
              total,
            })}
          </span>
          <button
            type="button"
            className="rounded border px-3 py-1 disabled:opacity-40"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          >
            {t("movimenti.previous")}
          </button>
          <button
            type="button"
            className="rounded border px-3 py-1 disabled:opacity-40"
            disabled={offset + PAGE_SIZE >= total}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            {t("movimenti.next")}
          </button>
        </div>
      )}
    </section>
  );
}
