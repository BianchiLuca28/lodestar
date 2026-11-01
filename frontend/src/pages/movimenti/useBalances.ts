import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { components } from "@/api/schema";

import { ApiError } from "./useTransactions";

export type AccountBalance = components["schemas"]["AccountBalance"];
export type BalanceCheck = components["schemas"]["BalanceCheckOut"];
export type BalanceCheckInput = components["schemas"]["BalanceCheckIn"];
export type BalancePreview = components["schemas"]["BalancePreview"];

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      key?: string;
      field?: string | null;
      message?: string;
    } | null;
    throw new ApiError(
      response.status,
      body?.key ?? "error.domain",
      body?.field ?? null,
      body?.message ?? `${url}: ${String(response.status)}`,
    );
  }
  return (await response.json()) as T;
}

function post<T>(url: string, body: unknown): Promise<T> {
  return json<T>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function useAccountBalances() {
  return useQuery({
    queryKey: ["balances"],
    queryFn: () => json<AccountBalance[]>("/api/accounts/balances"),
  });
}

export function useBalanceChecks() {
  return useQuery({
    queryKey: ["balance-checks"],
    queryFn: () => json<BalanceCheck[]>("/api/balance-checks"),
  });
}

export function usePreviewBalanceCheck() {
  return useMutation({
    mutationFn: (input: BalanceCheckInput) =>
      post<BalancePreview>("/api/balance-checks/preview", input),
  });
}

/** Records a check; reloads balances, checks and the ledger (an adjustment line may appear). */
export function useCreateBalanceCheck() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: BalanceCheckInput) => post<BalanceCheck>("/api/balance-checks", input),
    onSuccess: () =>
      Promise.all(
        ["balances", "balance-checks", "transactions"].map((key) =>
          client.invalidateQueries({ queryKey: [key] }),
        ),
      ),
  });
}
