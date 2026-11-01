import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";

import "@/i18n";

export const HEALTH = {
  status: "ok",
  version: "0.0.1",
  llm: { reachable: true, base_url: "http://127.0.0.1:11434" },
  database: { reachable: true, revision: "0001" },
};

export const CONFIG = {
  accounts: [
    { name: "Banca Aurora", type: "bank", bucket: "P1", is_default: true },
    { name: "Contanti", type: "cash", bucket: "P1", is_default: false },
  ],
  categories: [
    { name: "🍝 Ristoranti", discretionary: true, subcategories: ["Pizzeria"] },
    { name: "💰 Stipendio", discretionary: false, subcategories: [] },
  ],
};

type Handler = (url: URL) => unknown;

/** Stub fetch: the handler for the longest matching path prefix answers with JSON. */
export function mockApi(routes: Record<string, unknown | Handler>) {
  const all: Record<string, unknown | Handler> = {
    "/api/health": HEALTH,
    "/api/config": CONFIG,
    "/api/transactions": { items: [], total: 0 },
    ...routes,
  };
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = new URL(String(input), "http://localhost");
    const key = Object.keys(all)
      .filter((path) => url.pathname.startsWith(path))
      .sort((a, b) => b.length - a.length)[0];
    if (key === undefined) return Promise.resolve(new Response("not found", { status: 404 }));
    const value = all[key];
    if (value instanceof Error) return Promise.resolve(new Response("boom", { status: 500 }));
    const body = typeof value === "function" ? (value as Handler)(url) : value;
    return Promise.resolve(new Response(JSON.stringify(body)));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** The query strings sent to a path, in call order. */
export function calls(fetchMock: ReturnType<typeof mockApi>, path: string): URLSearchParams[] {
  return fetchMock.mock.calls
    .map(([input]) => new URL(String(input), "http://localhost"))
    .filter((url) => url.pathname === path)
    .map((url) => url.searchParams);
}

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

/** Render one page at `path` with a fresh query client and a probe showing the current URL. */
export function renderPage(element: ReactElement, path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="*" element={element} />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
