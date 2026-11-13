import { useState } from "react";
import { useTranslation } from "react-i18next";

import { todayRome } from "@/lib/format";
import { useConfig } from "@/pages/movimenti/useTransactions";

import { DraftCard } from "./DraftCard";
import { hasDuplicate, useDraftMutations, usePendingDrafts } from "./useDrafts";

export function InboxPage() {
  const { t } = useTranslation();
  const drafts = usePendingDrafts();
  const config = useConfig();
  const { edit, approve, reject, approveMany } = useDraftMutations();
  const [skipped, setSkipped] = useState<number | null>(null);

  const items = drafts.data ?? [];
  const clean = items.filter((d) => !hasDuplicate(d));
  const busy = approve.isPending || reject.isPending || approveMany.isPending;

  function approveAll() {
    setSkipped(items.length - clean.length);
    approveMany.mutate(clean.map((d) => d.id));
  }

  return (
    <section className="p-6">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">{t("nav.inbox")}</h1>
        {clean.length > 0 && (
          <button
            type="button"
            disabled={busy}
            className="rounded bg-neutral-900 px-3 py-2 text-sm text-white disabled:opacity-50"
            onClick={approveAll}
          >
            {t("inbox.approveAll", { count: clean.length })}
          </button>
        )}
      </header>

      {skipped !== null && skipped > 0 && (
        <p className="mb-3 text-sm text-amber-800">{t("inbox.skipped", { count: skipped })}</p>
      )}
      {drafts.isPending && <p className="text-sm text-gray-500">{t("inbox.loading")}</p>}
      {drafts.isError && <p className="text-sm text-red-700">{t("inbox.error")}</p>}
      {drafts.isSuccess && items.length === 0 && (
        <p className="text-sm text-gray-500">{t("inbox.empty")}</p>
      )}

      {config.data && (
        <div className="flex flex-col gap-3">
          {items.map((draft) => (
            <DraftCard
              key={draft.id}
              draft={draft}
              config={config.data}
              today={todayRome()}
              busy={busy}
              onEdit={(lines) => edit.mutateAsync({ id: draft.id, lines })}
              onApprove={() => approve.mutate(draft.id)}
              onReject={() => reject.mutate(draft.id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
