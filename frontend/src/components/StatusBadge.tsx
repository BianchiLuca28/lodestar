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

export function StatusBadge() {
  const { t } = useTranslation();
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });

  const label = isError
    ? t("status.offline")
    : data
      ? t("status.online", { version: data.version })
      : t("status.checking");

  return (
    <span
      className={cn(
        "rounded-full px-3 py-1 text-xs",
        isError ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800",
      )}
    >
      {label}
    </span>
  );
}
