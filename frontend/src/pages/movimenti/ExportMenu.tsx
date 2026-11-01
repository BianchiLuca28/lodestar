import { useTranslation } from "react-i18next";

import type { FilterValues } from "./Filters";

const FORMATS = [
  { format: "csv", labelKey: "movimenti.export.csv" },
  { format: "xlsx", labelKey: "movimenti.export.xlsx" },
] as const;

function exportUrl(format: string, filters: FilterValues): string {
  const params = new URLSearchParams({ format });
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  return `/api/transactions/export?${params.toString()}`;
}

/** Download links for the ledger with the current filters; the browser does the download. */
export function ExportMenu({ filters }: { filters: FilterValues }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-600">{t("movimenti.export.label")}</span>
      {FORMATS.map(({ format, labelKey }) => (
        <a
          key={format}
          href={exportUrl(format, filters)}
          download
          className="rounded border border-gray-300 px-2 py-1 hover:bg-gray-50"
        >
          {t(labelKey)}
        </a>
      ))}
    </div>
  );
}
