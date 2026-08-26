# Architecture

## System overview

```
User (browser, Vercel-hosted Next.js 15)
  ├─ instant filtered reads ←── Supabase Postgres (cached dataset, RLS)
  ├─ auth (magic link / Google OAuth) ←── Supabase Auth
  ├─ "Research this" button ─→ Next.js route handler (rate-limited)
  │        └─→ GitHub repository_dispatch event (free) ─→ GitHub Actions runner
  │                                                            │
  │                    apps/agent pipeline (Python, uv):
  │                      1. country pack + depth level lookup
  │                      2. university inventory from official registries
  │                         (ROR / ETER / national lists)
  │                      3. per-university sitemap.xml keyword harvest
  │                         + Tavily search layer (paginated to depth cap)
  │                      4. adaptive fetch router:
  │                         static httpx probe → Playwright escalation
  │                         → Crawl4AI tier; best engine per domain remembered
  │                      5. Pydantic schema-constrained LLM extraction
  │                         (citation REQUIRED per field)
  │                      6. scholarship ↔ program cross-matching
  │                      7. QC gate (spec §42 checklist)
  │                      8. idempotent upsert + diff → change_log
  │                      9. progress rows → Supabase Realtime → UI drawer
  └─ exports: CSV/XLSX/JSON generated client-side (SheetJS)
```

## Read path (hot)

1. Client applies filters → PostgREST query through `@supabase/ssr` client.
2. Indexes on filter columns (funding_class, deadline_status, country_id, field_tags GIN) keep typical queries < 300 ms.
3. Matching/scoring runs client-side in `apps/web/src/lib` (pure TS) over fetched rows using user-adjustable weights — no server round-trip for re-scoring.

## Research trigger path

1. Signed-in user requests research for country set + depth level.
2. Route handler validates (zod), enforces per-user rate limits and dedupes active jobs (`research_jobs` row status=PENDING), then calls GitHub API `repository_dispatch` type `research-request` with payload `{countries, depth, job_id}` using a fine-grained PAT stored server-side.
3. Actions runner executes pipeline; updates `research_jobs.progress` as it works; UI subscribes via Supabase Realtime.
4. On completion: job row → DONE/FAILED with summary; new data visible immediately.

## Adaptive fetch routing (apps/agent/engines)

- First visit to any domain = static fetch (httpx + lxml). Success heuristics: HTTP 200 + meaningful text density + expected selector hits.
- Failure modes escalate: JS shell detected (tiny body, root-div only) or 403/challenge → Playwright-Python tier; still failing or markdown-quality needed → Crawl4AI tier (optional extra, presence-detected).
- Outcome stored in `domain_fetch_stats(best_engine, failure_counts, last_success)`; future visits go straight to the winning engine. Politeness: Scrapy autothrottle + robots.txt + per-domain concurrency caps everywhere.

## Depth levels

| Level | Search pages visited | Sitemap harvest | Per-domain page cap | Typical runtime |
|---|---|---|---|---|
| L1 Quick | top 3 | known portals only | 15 | minutes |
| L2 Standard | top 6 | all universities | 40 | ~1-2 h |
| L3 Exhaustive | up to 10 | full sitemaps | 100+ | hours |

L2 is the default; L3 is opt-in (cost/time control).

## Data integrity enforcement points

1. Extraction schemas require `{value, source_url, quote}` triples — validator rejects uncited critical fields to `NOT_SPECIFIED`.
2. Conflict capture: same field from multiple sources stored together with tiers; display prefers newest Tier-1, flags conflicts.
3. QC gate before publish (spec §42 checklist encoded in `pipelines/qc.py`).
4. Freshness: `last_verified_at`; >90 days ⇒ re-verification badge; refresh jobs diff into `change_log`.

## Deployment topology ($0)

- Vercel hobby: web app + route handlers. Env: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, server-only GitHub PAT.
- Supabase free tier: Postgres, Auth, Realtime. RLS on all tables (public read dataset, owner-only user tables).
- GitHub Actions: CI (lint/typecheck/test/build) + research runner (workflow_dispatch inputs: countries CSV, depth, dry_run; repository_dispatch listener). Concurrency group prevents overlapping runs.

## Security model

- Service-role key exists ONLY inside Actions runner env / never in browser.
- RLS: `select` public on dataset tables; inserts/updates restricted to service role; user tables owner-only.
- All external input zod-validated; scraped snippets rendered as inert text (no HTML injection).
- Rate limits: research triggers ≤ 2 active jobs/user; export endpoints unauthenticated but size-capped.
