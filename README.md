# EuropaGrad

Find, verify, filter, rank, track, and export funded European Master's programs for Bangladeshi CSE students — evidence-cited data produced by a Python research agent, served through a fast Next.js app. Every fact carries its source.

**Start here:** [AGENTS.md](AGENTS.md) → [docs/state.md](docs/state.md) → [docs/tasks.md](docs/tasks.md)

## Quick start

```powershell
npm i -g pnpm
pnpm install
cd apps/agent; uv sync
cd ../..
copy .env.example apps\web\.env.local
copy .env.example apps\agent\.env
```

Fill keys (see `.env.example`): Supabase URL + anon + service key (required), `OPENROUTER_API_KEY` + `TAVILY_API_KEY` (real LLM extraction + search; runs work keyless at heuristic quality), optional `JINA_API_KEY`, `DATABASE_URL`, `GITHUB_TOKEN` + `GITHUB_REPO` (in-app research trigger).

Apply the database schema:

```powershell
node --env-file=apps/agent/.env scripts/apply-migration.mjs
```

## Run the app

```powershell
pnpm dev        # http://localhost:3000
```

## Run research

```powershell
cd apps/agent
uv run agent doctor                        # verify keys
uv run agent run --countries IT --depth L1 --limit 5   # real run, writes cited data
uv run agent run --countries IT --depth L2 --dry-run   # plan only
```

Depth: L1 quick (minutes) → L2 standard (1–2h) → L3 exhaustive (hours).
Or dispatch from the app: sign in → Results → "Start research" (requires `GITHUB_TOKEN` + `GITHUB_REPO` configured).

## Verify / test

```powershell
pnpm lint && pnpm typecheck && pnpm test && pnpm build     # web
cd apps/agent; uv run ruff check .; uv run pytest -q       # agent
node --env-file=apps/agent/.env scripts/test-rls.mjs       # DB security policies (from repo root)
node --env-file=apps/agent/.env scripts/check-taxonomy-drift.mjs
cd apps/web; pnpm e2e                                      # browser journeys (Playwright)
```

## Architecture (one paragraph)

Next.js 15 app on Vercel reads a Supabase Postgres dataset; a Python agent (Scrapy-style static fetch → Jina Reader → Playwright → Crawl4AI escalation, Tavily/DDG/Jina search, citation-enforced LLM extraction) researches universities and writes evidence-cited rows; runs execute on GitHub Actions or locally. Details: [docs/architecture.md](docs/architecture.md), [docs/pipeline.md](docs/pipeline.md), [docs/data-model.md](docs/data-model.md).
