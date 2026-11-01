import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";

import "@/i18n";

import { StatusBadge } from "./StatusBadge";

function renderBadge() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <StatusBadge />
    </QueryClientProvider>,
  );
}

function stubHealth(llmReachable: boolean) {
  const body = {
    status: "ok",
    version: "0.0.1",
    llm: { reachable: llmReachable, base_url: "http://127.0.0.1:11434" },
  };
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(body))));
}

afterEach(() => vi.unstubAllGlobals());

it("shows backend and LLM online", async () => {
  stubHealth(true);

  renderBadge();

  expect(await screen.findByText("Backend attivo · v0.0.1")).toBeInTheDocument();
  expect(screen.getByText("LLM attivo")).toBeInTheDocument();
});

it("shows the LLM as unreachable while the backend is up", async () => {
  stubHealth(false);

  renderBadge();

  expect(await screen.findByText("Backend attivo · v0.0.1")).toBeInTheDocument();
  expect(screen.getByText("LLM non raggiungibile")).toBeInTheDocument();
});

it("shows the backend as offline when /api/health fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

  renderBadge();

  expect(await screen.findByText("Backend non raggiungibile")).toBeInTheDocument();
  expect(screen.queryByText(/LLM/)).not.toBeInTheDocument();
});
