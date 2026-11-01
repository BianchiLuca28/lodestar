import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import type { components } from "@/api/schema";
import { cn } from "@/lib/utils";

type HealthResponse = components["schemas"]["HealthResponse"];

async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/health");
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return (await response.json()) as HealthResponse;
}

function Pill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={cn(
        "rounded-full px-3 py-1 text-xs",
        ok ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800",
      )}
    >
      {label}
    </span>
  );
}

export function StatusBadge() {
  const { t } = useTranslation();
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });

  if (isError) return <Pill ok={false} label={t("status.offline")} />;
  if (!data) return <Pill ok label={t("status.checking")} />;

  return (
    <div className="flex gap-2">
      <Pill ok label={t("status.online", { version: data.version })} />
      <Pill
        ok={data.llm.reachable}
        label={data.llm.reachable ? t("status.llmOnline") : t("status.llmOffline")}
      />
    </div>
  );
}
