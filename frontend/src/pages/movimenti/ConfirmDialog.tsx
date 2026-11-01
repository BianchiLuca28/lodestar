import { useEffect, useId, useRef } from "react";
import { useTranslation } from "react-i18next";

/** A small modal asking to confirm a destructive action. Escape cancels. */
export function ConfirmDialog({
  message,
  confirmLabel,
  error,
  busy,
  onConfirm,
  onCancel,
}: {
  message: string;
  confirmLabel: string;
  error?: string | null;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const { t } = useTranslation();
  const titleId = useId();
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    confirmRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/30">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="w-80 rounded bg-white p-4 shadow-lg"
      >
        <p id={titleId} className="mb-3">
          {message}
        </p>
        {error && <p className="mb-3 text-sm text-red-700">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" className="rounded border px-3 py-1 text-sm" onClick={onCancel}>
            {t("movimenti.cancel")}
          </button>
          <button
            ref={confirmRef}
            type="button"
            disabled={busy}
            className="rounded bg-red-700 px-3 py-1 text-sm text-white disabled:opacity-50"
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
