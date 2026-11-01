import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { components, operations } from "@/api/schema";

export type Transaction = components["schemas"]["TransactionOut"];
export type TransactionPage = components["schemas"]["TransactionPage"];
export type TransactionInput = components["schemas"]["TransactionIn"];
export type AppConfig = components["schemas"]["ConfigResponse"];
export type TransactionQuery = NonNullable<
  operations["list_transactions_api_transactions_get"]["parameters"]["query"]
>;

export const PAGE_SIZE = 50;

/** An error answered by the API, with the i18n key and the field it concerns. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly key: string,
    readonly field: string | null,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
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
      body?.message ?? `${url}: ${response.status}`,
    );
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}

function send<T>(method: string, url: string, body?: unknown): Promise<T> {
  return request<T>(url, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function useConfig() {
  return useQuery({
    queryKey: ["config"],
    queryFn: () => request<AppConfig>("/api/config"),
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
    queryFn: () => request<TransactionPage>(`/api/transactions?${params.toString()}`),
    placeholderData: keepPreviousData,
  });
}

/** Create, update and delete; each reloads the transactions list when it succeeds. */
export function useTransactionMutations() {
  const client = useQueryClient();
  const onSuccess = () => client.invalidateQueries({ queryKey: ["transactions"] });
  return {
    create: useMutation({
      mutationFn: (input: TransactionInput) =>
        send<Transaction>("POST", "/api/transactions", input),
      onSuccess,
    }),
    update: useMutation({
      mutationFn: ({ id, input }: { id: number; input: TransactionInput }) =>
        send<Transaction>("PATCH", `/api/transactions/${String(id)}`, input),
      onSuccess,
    }),
    remove: useMutation({
      mutationFn: (id: number) => send<undefined>("DELETE", `/api/transactions/${String(id)}`),
      onSuccess,
    }),
  };
}
