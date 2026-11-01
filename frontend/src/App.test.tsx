import { render, screen, within } from "@testing-library/react";

import { App } from "./App";

const PAGES = [
  { path: "/", title: "Panoramica" },
  { path: "/inbox", title: "Inbox" },
  { path: "/movimenti", title: "Movimenti" },
  { path: "/portafoglio", title: "Portafoglio" },
  { path: "/piano", title: "Piano" },
  { path: "/chat", title: "Chat" },
];

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(
        JSON.stringify({
          status: "ok",
          version: "0.0.1",
          llm: { reachable: true, base_url: "http://127.0.0.1:11434" },
        }),
      )),
  );
});

afterEach(() => vi.unstubAllGlobals());

it("shows the six pages in the nav, in Italian", () => {
  render(<App initialPath="/" />);

  const nav = screen.getByRole("navigation");
  const labels = within(nav)
    .getAllByRole("link")
    .map((link) => link.textContent);
  expect(labels).toEqual(PAGES.map((page) => page.title));
});

it.each(PAGES)("renders the $title page at $path", ({ path, title }) => {
  render(<App initialPath={path} />);

  expect(screen.getByRole("heading", { level: 1, name: title })).toBeInTheDocument();
});
