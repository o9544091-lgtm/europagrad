# EuropaGrad — Agent Handbook

Master context for ANY model or developer working in this repo. Read this file fully before touching code, then read `docs/state.md` (current status) and `docs/tasks.md` (work queue).

## What this product is

EuropaGrad is a research-grade web app that helps Bangladeshi CSE students discover, verify, filter, rank, track, and export European Master's programs and scholarships (plus US/AU extras). A Python research agent produces **evidence-cited data**; a Next.js app provides instant filtering/matching/tracking over that data. Full product spec: see plan summary in `docs/state.md` decisions log and `docs/architecture.md`.

## Golden rules (never violate)

1. **Never fabricate data.** Every program/scholarship fact must trace to a source URL + verbatim quote stored as evidence. No citation = field stays `NOT_SPECIFIED`.
2. "Not specified on official source" is NEVER interpreted as "not required".
3. Funding taxonomy is precise: fully funded ≠ tuition-free ≠ waiver ≠ low tuition. Never label anything "fully funded" without supporting evidence.
4. Distinguish program deadline vs scholarship deadline; keep CLOSED items visible, never silently delete.
5. Prefer newest OFFICIAL source (tier order: Gov > University > Scholarship org > EU org > portal > blog/forum); flag conflicts, never silently pick one.
6. Match language: "Likely eligible based on published requirements" — never guarantee admission.
7. Respect robots.txt and per-domain rate limits when crawling.
8. Secrets only via environment variables; never commit `.env`, never log key values.

Detailed rules: load the `data-integrity` skill whenever editing agent extraction/storage or result display code.

## Operational rules (hard constraints)

1. **One agent at a time.** Never launch parallel subagents/Task calls. One agent finishes before another starts.
2. **One terminal at a time.** Never issue parallel shell/background commands. Run one command, wait for it to finish, then the next.
3. **One task at a time.** Work exactly one docs/tasks.md item; complete or explicitly park it (with a ledger note) before touching another. No batched multi-task work.

## Stack

| Layer | Tech |
|---|---|
| Web app | Next.js 15 App Router, TypeScript strict, Tailwind CSS v4, shadcn/ui |
| DB/Auth/Realtime | Supabase (Postgres + Auth magic link/Google + Realtime) |
| Research agent | Python 3.12+, Scrapy core, httpx/lxml static tier, Playwright-Python escalation tier, Crawl4AI optional tier, Pydantic schemas, OpenRouter LLM, Tavily search |
| Agent runtime | GitHub Actions (`workflow_dispatch` / `repository_dispatch` / schedule) — free |
| Web hosting | Vercel (free hobby) |
| Exports | SheetJS client-side (CSV/XLSX/JSON) |

Coverage: 30 European countries + Erasmus Mundus joint degrees + Europe-wide mode + US/Australia. Seed countries researched deeply at launch: Germany, Italy, France, Netherlands, Sweden.

## Repo map

```
apps/web/            Next.js app (UI, API routes for job triggers)
  src/app/           Routes (see docs/ui-spec.md route map)
  src/lib/supabase/  Browser/server Supabase clients
  src/lib/           Matching/ranking logic (pure TS, unit-tested)
  src/components/    UI kit + feature components
apps/agent/          Python research pipeline
  src/europagrad_agent/
    cli.py           CLI entry (agent ... commands)
    config.py        Env-driven settings
    engines/         Adaptive fetch routing (task 6-7)
    registries/      University inventory loaders (task 8)
    search/          Tavily provider + query expansion (task 9)
    extraction/      Pydantic schemas + LLM extraction (task 10)
    pipelines/       Orchestrator, QC gate, upsert/diff (task 11)
    storage/         Supabase writers
    taxonomy.py      Enum mirrors of Postgres enums
.github/workflows/   ci.yml (lint/test/build), agent-research.yml (runner)
docs/                Architecture, data-model, pipeline, ui-spec, tasks, state
```

Contract between TS and Python sides = Postgres schema (single source of truth) + Pydantic JSON Schemas. TS types are generated from the DB schema (task 2). Never hand-duplicate enum values in both languages without updating migrations first.

## Setup (one-time)

Prereqs: Node >= 20 (pnpm enabled), Python >= 3.12, uv (`pip install uv`).

```powershell
npm i -g pnpm            # if pnpm missing
pnpm install             # web deps
uv sync                  # agent deps (run inside apps/agent; add --extra browser for Playwright tier)
```

Copy `.env.example` → `apps/web/.env.local` and `apps/agent/.env`; fill keys (Supabase URL/anon key required for app; OpenRouter + Tavily keys required for agent runs).

Playwright browsers (escalation tier): `cd apps/agent; uv sync --extra browser; uv run playwright install chromium`

## Daily workflow (how to continue work)

1. Read `AGENTS.md` (this file) + `docs/state.md`.
2. Open `docs/tasks.md`; pick the lowest-numbered ⬜ task whose dependencies are met.
3. Implement to its Acceptance Criteria. Follow conventions below. Load relevant skills first (`data-integrity` for pipeline/data code, `ui-drop-in` when integrating externally generated UI).
4. Verify: `pnpm lint && pnpm typecheck && pnpm test` (web) and `uv run ruff check . && uv run pytest -q` (agent). Fix failures at root cause.
5. Update `docs/tasks.md` status (⬜→☑ or 🚧) and `docs/state.md` (phase, decisions, known bugs) in the same change.
6. Report outcomes ("Task 9 done: Tavily provider paginates to N pages, mocked tests green"), not activity logs.

Slash commands available: `/next-task`, `/run-research`, `/qa-pass`.

## Conventions

- TypeScript strict; no `any`; components typed with explicit prop interfaces; files kebab-case, components PascalCase.
- Python: ruff format+lint line-length 100; type hints on public functions.
- No TODO comments left in code — open work lives in `docs/tasks.md`.
- No placeholder/fake functionality in merged work; scaffold stubs must name their owning task number.
- Conventional commits (`feat(web):`, `feat(agent):`, `fix:`, `docs:`).
- Tests live beside code; every matching/ranking/extraction rule needs unit coverage including edge cases.

## Definition of done

Implemented + integrated + validated (AC met) + lint/typecheck/tests green + responsive + error/loading states handled + docs/tasks.md and docs/state.md updated.
