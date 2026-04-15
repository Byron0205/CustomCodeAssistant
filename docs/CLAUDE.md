# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Rules

1. Think before acting. Read existing files before writing code.
2. Be concise in output but thorough in reasoning.
3. Prefer editing over rewriting whole files.
4. Do not re-read files you have already read unless the file may have changed.
5. Test your code before declaring done.
6. No sycophantic openers or closing fluff.
7. Keep solutions simple and direct.
8. User instructions always override this file.

## Commands

```bash
npm run dev      # Start dev server at http://localhost:3000
npm run build    # Production build
npm run lint     # Run ESLint (eslint v9, flat config)
```

No test runner is configured.

## Stack

- **Next.js 16.2.2** + **React 19.2.4** — App Router. Check `node_modules/next/dist/docs/` before writing Next.js code (breaking changes from earlier versions).
- **TailwindCSS v4** — PostCSS-based, no `tailwind.config.*` file; config lives in CSS.
- **React Query v5** (`@tanstack/react-query`) — all async data fetching goes through it. Query client is initialized in `src/app/providers.tsx`.
- **TypeScript strict** mode.

## Architecture

### Routes
- `/` → `src/app/page.tsx` — Dashboard with KPI cards and posts table.
- `/upload` → `src/app/upload/page.tsx` — CSV import flow with three stages: `idle → preview → success`.

### Layout
`src/app/layout.tsx` wraps everything in `<Providers>` (React Query) then `<SidebarShell>` (collapsible sidebar). The sidebar width drives a margin on the content area (`ml-60` / `ml-16`).

### Data layer
`src/services/api.ts` — currently all mock data with a simulated random delay. `getPosts()` and `getPostStats()` are the two query functions. When real API calls are added, the shape must match the types in `src/interface/IPost.ts`.

### Types
All domain types live in `src/interface/`:
- `IPost.ts` — `Post`, `PostWithStats`, `PostStats`, `Platform`, `EngagementStatus`
- `ICsv.ts` — `CsvParseResult`, `CsvRowError`
- `IKpiCard.ts` — props for the KPI card component

### Business logic (`src/lib/utils.ts`)
Engagement rate = `(likes + comments + saves) / reach * 100`. Thresholds: excellent ≥ 5%, good ≥ 3%, fair ≥ 1%, low < 1%.

### CSV import (`src/lib/csv.ts`)
`parsePostsCSV()` validates headers and per-row data, returning `{ posts, errors }`. Required columns: `platform, description, date, reach, likes, comments, saves`. After import, the upload page invalidates `['posts']` and `['postStats']` React Query keys to refresh the dashboard.