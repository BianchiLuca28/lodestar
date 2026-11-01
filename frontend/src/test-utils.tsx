/* eslint-disable react-refresh/only-export-components -- test helpers, never hot-reloaded */
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

type Handler = (url: URL, init?: RequestInit) => unknown;

/** A canned response with a status other than 200. */
export class Reply {
  constructor(
    readonly status: number,
    readonly body: unknown = null,
  ) {}
}

/**
 * Stub fetch. Keys are a path prefix ("/api/transactions") or a method plus prefix
 * ("POST /api/transactions"); the longest match wins, method-specific keys first.
 * Values are a JSON body, a Reply, an Error (500) or a handler returning either.
 */
export function mockApi(routes: Record<string, unknown>) {
  const all: Record<string, unknown> = {
    "/api/health": HEALTH,
    "/api/config": CONFIG,
    "/api/transactions": { items: [], total: 0 },
    ...routes,
  };
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://localhost");
    const method = (init?.method ?? "GET").toUpperCase();
    const matches = (key: string) => {
      const [m, path] = key.includes(" ") ? key.split(" ") : [undefined, key];
      return (m === undefined || m === method) && url.pathname.startsWith(path ?? "");
    };
    const key = Object.keys(all)
      .filter(matches)
      .sort((a, b) => Number(b.includes(" ")) - Number(a.includes(" ")) || b.length - a.length)[0];
    if (key === undefined) return Promise.resolve(new Response("not found", { status: 404 }));
    let value = all[key];
    if (typeof value === "function") value = (value as Handler)(url, init);
    if (value instanceof Error) return Promise.resolve(new Response("boom", { status: 500 }));
    if (value instanceof Reply) {
      const body = value.status === 204 ? null : JSON.stringify(value.body);
      return Promise.resolve(new Response(body, { status: value.status }));
    }
    return Promise.resolve(new Response(JSON.stringify(value)));
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

/** The query string of the last call to a path; fails the test if there was none. */
export function lastCall(fetchMock: ReturnType<typeof mockApi>, path: string): URLSearchParams {
  const last = calls(fetchMock, path).at(-1);
  if (last === undefined) throw new Error(`no call to ${path}`);
  return last;
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

/** The calls made with a method to a path: [url, parsed JSON body]. */
export function sent(
  fetchMock: ReturnType<typeof mockApi>,
  method: string,
  path: string,
): [URL, unknown][] {
  return fetchMock.mock.calls
    .filter(([, init]) => (init?.method ?? "GET").toUpperCase() === method)
    .map(([input, init]) => {
      const body = typeof init?.body === "string" ? (JSON.parse(init.body) as unknown) : null;
      return [new URL(String(input), "http://localhost"), body] as [URL, unknown];
    })
    .filter(([url]) => url.pathname.startsWith(path));
}
