import { useState } from "react";
import { useTranslation } from "react-i18next";

import { type Direction, formatDate, formatSignedMoney } from "@/lib/format";
import { TransactionForm } from "@/pages/movimenti/TransactionForm";
import type { AppConfig, Transaction, TransactionInput } from "@/pages/movimenti/useTransactions";

import type { Draft, DraftLine } from "./useDrafts";

function directionOf(line: DraftLine): Direction {
  if (line.from_account && line.to_account) return "transfer";
  return line.from_account ? "expense" : "income";
}

function accounts(line: DraftLine): string {
  if (line.from_account && line.to_account) return `${line.from_account} → ${line.to_account}`;
  return line.from_account ?? line.to_account ?? "";
}

function input(line: DraftLine): TransactionInput {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- dropping the field
  const { possible_duplicates, ...rest } = line;
  return rest;
}

/** TransactionForm edits ledger lines; a draft line gets the fields a stored one would have. */
function asTransaction(line: DraftLine): Transaction {
  return {
    ...input(line),
    amount: String(line.amount),
    id: 0,
    direction: directionOf(line),
    source: "telegram",
    created_at: "",
  };
}

export function DraftCard({
  draft,
  config,
  today,
  busy,
  onEdit,
  onApprove,
  onReject,
}: {
  draft: Draft;
  config: AppConfig;
  today: string;
  busy: boolean;
  onEdit: (lines: TransactionInput[]) => Promise<unknown>;
  onApprove: () => void;
  onReject: () => void;
}) {
  const { t } = useTranslation();
  const [editing, setEditing] = useState<number | null>(null);

  async function save(index: number, edited: TransactionInput) {
    await onEdit(draft.lines.map((l, i) => (i === index ? edited : input(l))));
    setEditing(null);
  }

  return (
    <article className="rounded border border-gray-200 p-4">
      <header className="mb-3 flex items-baseline justify-between gap-4">
        <blockquote className="text-sm text-gray-800 italic">
          &ldquo;{draft.origin_text ?? "—"}&rdquo;
        </blockquote>
        <span className="shrink-0 text-xs text-gray-500">
          {t(`inbox.source.${draft.source}`)} · {formatDate(draft.created_at.slice(0, 10))}
          {draft.version > 1 && ` · ${t("inbox.version", { version: draft.version })}`}
        </span>
      </header>

      <ul className="mb-3 divide-y divide-gray-100">
        {draft.lines.map((line, index) =>
          editing === index ? (
            <li key={index} className="py-2">
              <TransactionForm
                config={config}
                initial={asTransaction(line)}
                today={today}
                onSubmit={(edited) => save(index, edited)}
                onCancel={() => setEditing(null)}
              />
            </li>
          ) : (
            <li key={index} className="flex items-center gap-3 py-2 text-sm">
              <span className="w-24">{formatDate(line.date)}</span>
              <span className="w-28 text-right tabular-nums">
                {formatSignedMoney(String(line.amount), directionOf(line))}
              </span>
              <span className="w-48 truncate">{accounts(line)}</span>
              <span className="flex-1 truncate">
                {line.category}
                {line.subcategory && ` · ${line.subcategory}`}
                {line.note && <span className="text-gray-500"> — {line.note}</span>}
              </span>
              {line.possible_duplicates.length > 0 && (
                <span
                  className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800"
                  title={t("inbox.duplicateOf", { ids: line.possible_duplicates.join(", ") })}
                >
                  {t("inbox.possibleDuplicate")}
                </span>
              )}
              <button
                type="button"
                aria-label={t("inbox.editLine")}
                className="text-gray-500 hover:text-gray-900"
                onClick={() => setEditing(index)}
              >
                ✏️
              </button>
            </li>
          ),
        )}
      </ul>

      <footer className="flex justify-end gap-2">
        <button
          type="button"
          aria-label={t("inbox.reject")}
          disabled={busy}
          className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
          onClick={onReject}
        >
          ❌ {t("inbox.reject")}
        </button>
        <button
          type="button"
          aria-label={t("inbox.approve")}
          disabled={busy || editing !== null}
          className="rounded bg-neutral-900 px-3 py-1 text-sm text-white disabled:opacity-50"
          onClick={onApprove}
        >
          ✅ {t("inbox.approve")}
        </button>
      </footer>
    </article>
  );
}
