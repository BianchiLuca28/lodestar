import { type FormEvent, useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";

import { formatMoney, parseAmount, todayRome } from "@/lib/format";

import { usePreviewBalanceCheck, useCreateBalanceCheck } from "./useBalances";
import { ApiError } from "./useTransactions";

const control = "rounded border border-gray-300 px-2 py-1 text-sm";

/** Parses a balance the user typed; unlike an amount, it may be negative (an overdraft). */
function parseBalance(input: string): string | null {
  const text = input.trim();
  const negative = text.startsWith("-") || text.startsWith("−");
  const parsed = parseAmount(negative ? text.slice(1) : text);
  if (parsed === null) return null;
  return negative && Number(parsed) !== 0 ? `-${parsed}` : parsed;
}

export function BalanceCheckDialog({
  account,
  onClose,
}: {
  account: string;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const ids = useId();
  const [date, setDate] = useState(todayRome());
  const [real, setReal] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const preview = usePreviewBalanceCheck();
  const create = useCreateBalanceCheck();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function input() {
    const parsed = parseBalance(real);
    if (parsed === null) {
      setLocalError(t("error.invalidAmount"));
      return null;
    }
    setLocalError(null);
    return { account, date, real_balance: parsed };
  }

  function calculate(event: FormEvent) {
    event.preventDefault();
    const body = input();
    if (body) preview.mutate(body);
  }

  function confirm() {
    const body = input();
    if (body) create.mutate(body, { onSuccess: onClose });
  }

  const apiError = preview.error ?? create.error;
  const error =
    localError ??
    (apiError instanceof ApiError ? t(apiError.key) : apiError ? t("error.domain") : null);
  const gap = preview.data ? Number(preview.data.gap) : null;

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/30">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${ids}-title`}
        className="w-96 rounded bg-white p-4 shadow-lg"
      >
        <h2 id={`${ids}-title`} className="mb-3 font-semibold">
          {t("movimenti.balances.dialogTitle", { account })}
        </h2>
        <form onSubmit={calculate} className="flex flex-col gap-3">
          <label htmlFor={`${ids}-date`} className="flex flex-col gap-1 text-xs text-gray-600">
            {t("movimenti.form.date")}
            <input
              id={`${ids}-date`}
              type="date"
              className={control}
              value={date}
              onChange={(e) => {
                setDate(e.target.value);
                preview.reset();
              }}
            />
          </label>
          <label htmlFor={`${ids}-real`} className="flex flex-col gap-1 text-xs text-gray-600">
            {t("movimenti.balances.real")}
            <input
              id={`${ids}-real`}
              inputMode="decimal"
              className={control}
              value={real}
              onChange={(e) => {
                setReal(e.target.value);
                preview.reset();
              }}
            />
          </label>
          {error && <p className="text-sm text-red-700">{error}</p>}
          {preview.data && gap !== null && (
            <div className="rounded bg-gray-50 p-2 text-sm">
              <p>
                {t("movimenti.balances.computed")}: {formatMoney(preview.data.computed)}
              </p>
              {gap === 0 ? (
                <p className="text-green-700">{t("movimenti.balances.noGap")}</p>
              ) : (
                <>
                  <p className={gap > 0 ? "text-green-700" : "text-red-700"}>
                    {t("movimenti.balances.gap")}: {formatMoney(preview.data.gap)}
                  </p>
                  <p className="text-xs text-gray-500">{t("movimenti.balances.adjustmentHint")}</p>
                </>
              )}
            </div>
          )}
          <div className="flex justify-end gap-2">
            <button type="button" className="rounded border px-3 py-1 text-sm" onClick={onClose}>
              {t("movimenti.cancel")}
            </button>
            {preview.data ? (
              <button
                type="button"
                disabled={create.isPending}
                className="rounded bg-blue-700 px-3 py-1 text-sm text-white disabled:opacity-50"
                onClick={confirm}
              >
                {t("movimenti.balances.confirm")}
              </button>
            ) : (
              <button
                type="submit"
                disabled={preview.isPending}
                className="rounded bg-blue-700 px-3 py-1 text-sm text-white disabled:opacity-50"
              >
                {t("movimenti.balances.calculate")}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
