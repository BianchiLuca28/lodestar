import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { formatDate, formatSignedMoney } from "@/lib/format";
import { cn } from "@/lib/utils";

import type { Transaction } from "./useTransactions";

const column = createColumnHelper<Transaction>();

const AMOUNT_COLOUR = {
  expense: "text-red-700",
  income: "text-green-700",
  transfer: "text-gray-500",
} as const;

function accounts(t: Transaction): string {
  if (t.from_account && t.to_account) return `${t.from_account} → ${t.to_account}`;
  return t.from_account ?? t.to_account ?? "";
}

export function TransactionsTable({ rows }: { rows: Transaction[] }) {
  const { t } = useTranslation();

  const columns = useMemo(
    () => [
      column.accessor("date", {
        header: t("movimenti.columns.date"),
        cell: (c) => formatDate(c.getValue()),
      }),
      column.accessor("amount", {
        header: t("movimenti.columns.amount"),
        cell: (c) => {
          const tx = c.row.original;
          return (
            <span className={cn("whitespace-nowrap tabular-nums", AMOUNT_COLOUR[tx.direction])}>
              {formatSignedMoney(tx.amount, tx.direction)}
            </span>
          );
        },
      }),
      column.display({
        id: "accounts",
        header: t("movimenti.columns.accounts"),
        cell: (c) => accounts(c.row.original),
      }),
      column.accessor("category", {
        header: t("movimenti.columns.category"),
        cell: (c) => (
          <div>
            <div>{c.getValue()}</div>
            {c.row.original.subcategory && (
              <div className="text-xs text-gray-500">{c.row.original.subcategory}</div>
            )}
          </div>
        ),
      }),
      column.accessor("note", { header: t("movimenti.columns.note") }),
      column.accessor("tag", {
        header: t("movimenti.columns.tag"),
        cell: (c) => (
          <div className="flex flex-wrap gap-1">
            {c.getValue() && (
              <span className="rounded bg-blue-50 px-2 text-xs text-blue-800">{c.getValue()}</span>
            )}
            {c.row.original.exclude_from_stats && (
              <span
                title={t("movimenti.excludedHint")}
                className="rounded bg-gray-100 px-2 text-xs text-gray-600"
              >
                {t("movimenti.excluded")}
              </span>
            )}
          </div>
        ),
      }),
    ],
    [t],
  );

  // TanStack Table v8 returns unmemoizable functions; the React Compiler skips this component.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({ data: rows, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        {table.getHeaderGroups().map((group) => (
          <tr key={group.id} className="border-b text-left text-xs text-gray-500">
            {group.headers.map((header) => (
              <th key={header.id} className="px-2 py-2 font-medium">
                {flexRender(header.column.columnDef.header, header.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map((row) => (
          <tr key={row.id} className="border-b border-gray-100 align-top">
            {row.getVisibleCells().map((cell) => (
              <td key={cell.id} className="px-2 py-2">
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
