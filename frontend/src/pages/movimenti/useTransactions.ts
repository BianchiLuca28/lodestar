import { keepPreviousData, useQuery } from "@tanstack/react-query";

import type { components, operations } from "@/api/schema";

export type Transaction = components["schemas"]["TransactionOut"];
export type TransactionPage = components["schemas"]["TransactionPage"];
export type AppConfig = components["schemas"]["ConfigResponse"];
export type TransactionQuery = NonNullable<
  operations["list_transactions_api_transactions_get"]["parameters"]["query"]
>;

export const PAGE_SIZE = 50;

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  return (await response.json()) as T;
}

export function useConfig() {
  return useQuery({
    queryKey: ["config"],
    queryFn: () => getJson<AppConfig>("/api/config"),
    staleTime: Infinity,
  });
}

export function useTransactions(query: TransactionQuery) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  return useQuery({
    queryKey: ["transactions", query],
    queryFn: () => getJson<TransactionPage>(`/api/transactions?${params.toString()}`),
    placeholderData: keepPreviousData,
  });
}
