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

afterEach(() => vi.unstubAllGlobals());

it("shows the backend as online when /api/health answers ok", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok", version: "0.0.1" }))),
  );

  renderBadge();

  expect(await screen.findByText("Backend attivo · v0.0.1")).toBeInTheDocument();
});

it("shows the backend as offline when /api/health fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

  renderBadge();

  expect(await screen.findByText("Backend non raggiungibile")).toBeInTheDocument();
});
