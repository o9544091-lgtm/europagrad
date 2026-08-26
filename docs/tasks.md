# Task Ledger

Update protocol: flip ⬜→🚧 when starting, →☑ when Acceptance Criteria met AND lint/typecheck/tests green. Never skip numbers. Blocked tasks: add one-line reason after the task.

Legend: ⬜ pending · 🚧 in progress · ☑ done · ⊘ cancelled

## Phase 0-1 — Foundation
1. ☑ Scaffold repo: apps/web (Next.js 15 + TS + Tailwind), apps/agent (Python/uv); lint/format configs; CI stubs; docs suite; MCP config (chrome-devtools, context7). **AC:** structure per AGENTS.md repo map; installs verified.
2. ☑ Supabase project + schema migrations applied and verified: 13 tables, 8 enums, 32 countries seeded (5 launch seeds), 13 RLS policies; anon-key read path confirmed via PostgREST. Migration file: `supabase/migrations/0001_init.sql` (apply via `node --env-file=.env scripts/apply-migration.mjs` with DATABASE_URL set, or Dashboard SQL Editor). TS type generation from DB folded into task 3. **AC:** schema live; verified by script + REST query.
3. ☑ Taxonomy sync: all 8 Postgres enums mirrored in `apps/web/src/lib/db-types.ts` (TS) and `apps/agent/.../taxonomy.py` (Pydantic `ALL_ENUMS`); drift checker `scripts/check-taxonomy-drift.mjs` verifies live DB vs TS vs PY — all in sync; wired into CI agent job (runs when DATABASE_URL secret present). **AC:** drift check exits 1 on mismatch; verified green against live DB; 5/5 pytest, typecheck clean.
4. ☑ Auth (magic link + Google) guest-browse-all; RLS per data-model matrix; policy tests. *Delivered: middleware session refresh, /auth/callback code exchange, /auth/sign-out, auth dialog (email validation, Google button with graceful not-enabled toast), user menu in shell, plan-page prompt wired. Verified: 11/11 SQL-level RLS policy tests (scripts/test-rls.mjs), 8/8 API-level auth e2e (apps/web/scripts/auth-e2e.mjs), browser dialog + validation + live OTP acceptance. Google activates once OAuth client credentials are added; magic-link email delivery is the only path needing a real inbox.* **AC:** guest reads dataset; users isolated.
5. ☑ App shell: nav, routing, theme, base UI kit, loading/empty/error components. **AC:** responsive shell mobile+desktop. *Delivered early via external UI drop-in (see state.md D11): AppShell nav, Nocturne theme, all 10 screens presentational on mock data.*

## Phase 2 — Agent pipeline core
6. ☑ Scrapy skeleton: static tier (httpx/lxml), robots+autothrottle, per-domain limits, domain_fetch_stats writer. *Delivered as engines/{base,politeness,quality,static}.py + storage/domain_stats.py (Supabase + memory impls). Politeness: robots.txt cache (RFC 9309 semantics incl. 401/403=disallow-all), per-domain throttle w/ crawl-delay honor, realistic UA. 17/17 pytest green incl. robots-disallow, 403/429/500 escalation triggers, JS-shell detection, link absolutization, throttle timing, stats flow.*
7. ☑ Playwright-Python escalation + Crawl4AI optional adapter; adaptive router w/ JS-shell detection. *Delivered: engines/{playwright_engine,crawl4ai_engine,router}.py. Router consults domain memory → STATIC probe → escalate on FetchError or unusable (JS-shell) result → remember winner. Import guards raise clean FetchError when optional tiers absent. 26/26 pytest incl. escalation-on-shell, error-escalation, memory-first routing, integration test with real StaticEngine over mock transport.*
8. ☑ Registry ingestion (ROR dump loader + API loader + merge) + sitemap keyword harvester + L1/L2/L3 profiles. *Delivered: registries/{ror,ror_dump,sitemap,depth}.py. Dump loader discovers latest Zenodo "ROR Data" release, caches 30d, streams 309MB JSON array with bounded memory (regression-tested for array+JSONL forms). LIVE VALIDATION: Estonia → 28 education institutions in 4.0s from real dump (matches actual HE landscape; ≥95% recall vs registry). Sitemap harvester: index expansion, keyword filter, caps, robots-respected. Note: ~46% of ROR education records lack domains — search layer covers those.* **AC:** met.
9. ☑ SearchProvider interface + Tavily impl (paginated) + §23 query expansion. *Delivered: search/provider.py. Tavily deep-page fetching upfront (1 request per page), rate-limit/error mapping, include_domains support. QueryExpansion covers programmes/scholarships/language/work/joint templates. 53/53 pytest, all mocked HTTP.*
10. ☑ LLM extraction: strict Pydantic schemas, citation-required validation (quote substring check), NOT_SPECIFIED enforcement, conflict capture. *Delivered: extraction/{schemas,service}.py. CitedValue[T] with verbatim-quote validation (exact + whitespace-normalized + fuzzy-window ≥0.95); ExtractionValidator drops fabricated fields (→ NOT_SPECIFIED upstream) while keeping valid ones; OpenRouter service with forced-quote prompt, temperature 0, tolerant payload parsing. 67/67 pytest incl. golden fixtures: fabricated quote ⇒ field dropped, valid bundle unchanged, mocked-LLM end-to-end.* **AC:** met.
11. ☑ Orchestrator (§38 flow): inventory→discovery→verify→cross-match→QC(§42)→diff/upsert; idempotent re-runs. *Delivered: pipelines/{orchestrator,qc}.py, storage/{writer,universities,job_progress}.py, scripts/dry_run_orchestrator.py. QC gate: CSE-relevance, deadline currency, zero-tuition-without-note, citation-wrapper integrity. Writer: dedupe-key upsert, per-field diff → change_log + sources, CLOSED-never-delete. LIVE VALIDATION vs polimi.it + unibo.it: real sitemaps (robots-declared + www-variant + gzip — three real-world quirks found and handled), real fetch, citation-validated extraction, DB upsert; second run updated without duplicating (IDEMPOTENCY OK). Heuristic-extractor artifact row deleted after proof. 75/75 pytest.* **AC:** met (LLM-grade extraction deferred to task 13 with keys).
12. ⬜ GitHub Actions runner: workflow_dispatch (countries, depth, dry_run) + repository_dispatch listener; secrets; concurrency group; progress writer. **AC:** manual dispatch completes L1 slice end-to-end with live progress rows.
13. ⬜ Seed pass: DE IT FR NL SE at L2 + Erasmus Mundus CS subset; human QC review vs §42. **AC:** ≥30 programs + ≥15 scholarships fully cited; zero uncited critical facts.

## Phase 3 — Core app (P0)
*Note: presentation layer for tasks 14-21 landed early via the external UI drop-in (mock-data driven). Remaining work per task = wiring Supabase data + real interactions.*

14. ⬜ Search configurator screen. **AC:** valid queries for all combos; invalid blocked w/ messages.
15. ⬜ Results engine + results table. **AC:** <300ms typical query; score ordering correct.
16. ⬜ Program/Scholarship/Country detail pages + evidence tables + staleness badges + change history. **AC:** every fact traces to source or explicit NOT_SPECIFIED.
17. ⬜ Matching + ranking modules (pure TS lib): rule engine, weighted scoring, Reach/Target/Safety; unit-tested edge cases. **AC:** deterministic; plain-language reasons rendered.
18. ⬜ On-demand research trigger UI → route handler (rate-limit, auth-gate, dedupe) → repository_dispatch; Realtime progress drawer. **AC:** unresearched country yields job, live logs, populated results.
19. ⬜ Shortlist + tracker board (spec §37 statuses), optimistic UI. **AC:** guest prompted sign-in; state persists cross-device.
20. ⬜ Export XLSX/CSV/JSON of filtered set (SheetJS client-side). **AC:** opens in Excel/Sheets matching on-screen data.
21. ⬜ Deadline intelligence: computed statuses, days remaining, approaching filter. **AC:** fixtures cover all six states.

## Phase 4 — Integration & hardening (P1)
22. ⬜ Erasmus/joint section + filter; excluded from single-country counts. **AC:** dedicated view correct.
23. ⬜ Country comparison + "best for my profile" Mode D ranking from packs. **AC:** ranked rationale w/ factor breakdown.
24. ⬜ Saved searches/presets; stale-refresh suggestions; change_log viewer. **AC:** preset reapplies identically; diff old→new shown.
25. ⬜ Report view (exec summary, funding groups, deadlines, strategy, sources) + print-to-PDF styles. **AC:** renders same data as app.
26. ⬜ Security pass: RLS audit, zod everywhere, XSS-safe snippet rendering, secret scoping, abuse rate limits. **AC:** checklist doc; no high findings.
27. ⬜ Performance: indexes, pagination, virtualized table, lazy audit. **AC:** Lighthouse ≥90 perf/a11y key pages.

## Phase 5 — QA & launch
28. ⬜ E2E (Playwright): guest journey, auth journey, research-trigger (mocked runner), empty/error states. **AC:** green CI.
29. ⬜ Accessibility + responsive sweep (keyboard-only, SR labels, 360-1440px). **AC:** no blockers.
30. ⬜ Deployment: Vercel envs, Supabase prod, Actions secrets, uptime check. **AC:** prod URL serves seed data; trigger works in prod.
31. ⬜ Docs: README quickstart, operator guide (add country/re-run at each depth), user FAQ. **AC:** fresh-machine setup succeeds from docs alone.
32. ⬜ Full self-review pass (PM/eng/QA/security/design lenses) + fix list executed.

## Deferred (P2)
Email deadline alerts · new-opportunity notifications · worldwide expansion beyond US/AU · community contributions/moderation · GPA-cutoff & ranking-tier filters (registry slots exist) · mobile app.

## External dependency note
UI screens may arrive pre-generated from v0 (see docs/ui-spec.md integration procedure + ui-drop-in skill). Tasks 14-21 integrate them; generation can happen in parallel any time after this file's commit.
