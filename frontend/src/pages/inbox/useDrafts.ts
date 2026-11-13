import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { components } from "@/api/schema";
import { request, send, type TransactionInput } from "@/pages/movimenti/useTransactions";

export type Draft = components["schemas"]["DraftOut"];
export type DraftLine = components["schemas"]["DraftLineOut"];

const PENDING = ["drafts", "pending"];

export function usePendingDrafts() {
  return useQuery({
    queryKey: PENDING,
    queryFn: () => request<Draft[]>("/api/drafts?status=pending"),
    refetchInterval: 30_000,
  });
}

/** Edit, approve and reject; each reloads the drafts, and approval also the ledger. */
export function useDraftMutations() {
  const client = useQueryClient();
  const reload = () => client.invalidateQueries({ queryKey: ["drafts"] });
  const reloadAll = async () => {
    await reload();
    await client.invalidateQueries({ queryKey: ["transactions"] });
  };
  const decide = (id: number, action: "approve" | "reject") =>
    send<Draft>("POST", `/api/drafts/${String(id)}/${action}`);
  return {
    edit: useMutation({
      mutationFn: ({ id, lines }: { id: number; lines: TransactionInput[] }) =>
        send<Draft>("PUT", `/api/drafts/${String(id)}/lines`, { lines }),
      onSuccess: reload,
    }),
    approve: useMutation({ mutationFn: (id: number) => decide(id, "approve"), onSuccess: reloadAll }),
    reject: useMutation({ mutationFn: (id: number) => decide(id, "reject"), onSuccess: reload }),
    /** Approve one after another, so a failure stops at a known draft. */
    approveMany: useMutation({
      mutationFn: async (ids: number[]) => {
        for (const id of ids) await decide(id, "approve");
      },
      onSettled: reloadAll,
    }),
  };
}

export function hasDuplicate(draft: Draft): boolean {
  return draft.lines.some((l) => l.possible_duplicates.length > 0);
}
