# Frontend

React + TypeScript (strict), Vite, `pnpm`. TanStack Query for server state, TanStack Table for tables, Tailwind + shadcn/ui for components, Recharts for charts, i18next for strings. Tests with Vitest + Testing Library; lint with ESLint.

## Pages

Exactly six routes, one folder each under `src/pages/`:

| Route | Page | Purpose |
| --- | --- | --- |
| `/inbox` | Inbox | Review and edit drafts, approve or reject |
| `/movimenti` | Movimenti | The ledger: filter, add, edit, export, balance checks |
| `/` | Panoramica | Month and year at a glance |
| `/portafoglio` | Portafoglio | Buckets vs target, positions, trades |
| `/piano` | Piano | Rule status, planned expenses, Regole form |
| `/chat` | Chat | Questions with cited sources |

A new feature becomes a section of one of these pages.

## Conventions

- **API types** are generated from the backend's OpenAPI schema (`pnpm gen:api`); never hand-write request or response types.
- **Strings** go through `t('page.key')`; `src/i18n/it.json` is the default, `en.json` mirrors it.
- **Money and dates** go through `src/lib/format.ts` (`Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' })`, `dd/MM/yyyy`).
- **Each page has one primary action**, placed top right.
- **Charts** answer one question each, stated in the chart title as a sentence.
- Server state lives in TanStack Query; local UI state in components. No global store until a real need appears.
