import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";

import { formatDate, formatMoney } from "@/lib/format";
import { cn } from "@/lib/utils";

import { BalanceCheckDialog } from "./BalanceCheckDialog";
import { type BalanceCheck, useAccountBalances, useBalanceChecks } from "./useBalances";

/** Computed balance per account, the last check, and a way to check it against reality. */
export function Balances() {
  const { t } = useTranslation();
  const balances = useAccountBalances();
  const checks = useBalanceChecks();
  const [checking, setChecking] = useState<string | null>(null);
  const close = useCallback(() => setChecking(null), []);

  // Checks come newest first: the first one per account is its latest.
  const latest = new Map<string, BalanceCheck>();
  for (const check of checks.data ?? []) {
    if (!latest.has(check.account)) latest.set(check.account, check);
  }

  if (!balances.data) return null;

  return (
    <section aria-labelledby="saldi-title" className="mb-6">
      <h2 id="saldi-title" className="mb-2 text-lg font-semibold">
        {t("movimenti.balances.title")}
      </h2>
      <ul className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
        {balances.data.map(({ account, balance }) => {
          const last = latest.get(account);
          return (
            <li
              key={account}
              aria-label={account}
              className="flex flex-col gap-1 rounded border border-gray-200 p-3"
            >
              <span className="text-xs text-gray-500">{account}</span>
              <span
                className={cn(
                  "text-lg tabular-nums",
                  Number(balance) < 0 ? "text-red-700" : "text-gray-900",
                )}
              >
                {formatMoney(balance)}
              </span>
              {last && (
                <span className="text-xs text-gray-500">
                  {t("movimenti.balances.lastCheck", {
                    date: formatDate(last.date),
                    gap: formatMoney(last.gap),
                  })}
                </span>
              )}
              <button
                type="button"
                className="mt-1 self-start text-xs text-blue-700 underline"
                onClick={() => setChecking(account)}
              >
                {t("movimenti.balances.check")}
              </button>
            </li>
          );
        })}
      </ul>
      {checking && <BalanceCheckDialog account={checking} onClose={close} />}
    </section>
  );
}
