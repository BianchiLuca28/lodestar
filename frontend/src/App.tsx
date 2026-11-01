import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { BrowserRouter, MemoryRouter, Route, Routes } from "react-router";

import "@/i18n";
import { Nav } from "@/components/Nav";
import { StatusBadge } from "@/components/StatusBadge";
import { PAGES } from "@/pages";

function Layout() {
  return (
    <div className="mx-auto max-w-6xl p-4">
      <header className="mb-6 flex items-center justify-between gap-4">
        <Nav />
        <StatusBadge />
      </header>
      <main>
        <Routes>
          {PAGES.map(({ key, path, Component }) => (
            <Route key={key} path={path} element={<Component />} />
          ))}
        </Routes>
      </main>
    </div>
  );
}

/** App shell. Pass `initialPath` to render in memory (tests); omit it to use the browser URL. */
export function App({ initialPath }: { initialPath?: string }) {
  const [client] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={client}>
      {initialPath === undefined ? (
        <BrowserRouter>
          <Layout />
        </BrowserRouter>
      ) : (
        <MemoryRouter initialEntries={[initialPath]}>
          <Layout />
        </MemoryRouter>
      )}
    </QueryClientProvider>
  );
}
