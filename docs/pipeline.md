# Research Pipeline Spec (apps/agent)

Implements spec §38 flow. Modules map 1:1 to tasks 6-11 in docs/tasks.md.

```
USER PROFILE (from research_jobs payload / defaults)
   ↓ COUNTRIES + DEPTH LEVEL
COUNTRY PACK lookup (cached; researched on miss)
   ↓
UNIVERSITY INVENTORY — registries/ (task 8)
   ROR + ETER datasets, per-country official registries config:
     DE: Hochschulkompass · IT: Universitaly · FR: Campus France etab list
     NL: studiekeuze/duo · SE/FI: university lists · fallback: Wikipedia+ROR diff
   Output: complete institution list w/ domains (target ≥95% recall)
   ↓
CANDIDATE URL HARVEST — per university
   a) sitemap.xml fetch → keyword filter:
      [master, msc, ma-, admission, international, tuition, fee, scholarship,
       english-taught, moi, requirements]
   b) Tavily search layer (search/, task 9): spec §23 query templates,
      paginated to depth cap; results merged into candidate set
   ↓
ADAPTIVE FETCH — engines/ (tasks 6-7)
   router(domain):
     stats = domain_fetch_stats[domain] or probe STATIC first
     if best_engine set → use it
     else try STATIC (httpx+lxml) → quality check (text density, selectors)
          fail → PLAYWRIGHT (JS shell / 403 / challenge detection)
          fail → CRAWL4AI (if extra installed; markdown output preferred for LLM)
     persist winner + failure counts
   Politeness: robots.txt, Scrapy autothrottle, per-domain delay ≥1s, UA string
   ↓
LLM EXTRACTION — extraction/ (task 10)
   Pydantic schemas: ProgramExtract, UniversityExtract, ScholarshipExtract, CountryPack
   Every critical field = {value, source_url, quote} — quote must be verbatim
   substring of fetched content (validator enforces via difflib ratio ≥0.95)
   Missing/unverifiable ⇒ NOT_SPECIFIED. Never infer "not required" from absence.
   Conflicts: keep all versions {value, tier, date}, flag has_conflict
   Model: OpenRouter chat completions with JSON-mode schema prompt; temperature 0
   ↓
CROSS-MATCH — pipelines/match.py (task 11)
   scholarship → eligible countries → eligible universities/programs
   → eligible field ∩ program.field_tags → nationality check (BD)
   → admission-first? separate application? → write program_scholarships rows
   ↓
QC GATE — pipelines/qc.py (spec §42 encoded as assertions + warnings report)
   real-university check vs registry · relevance · intake/deadline currency ·
   BD eligibility · funding evidence completeness · duplicates · uncited facts
   ↓
UPSERT + DIFF — storage/ (task 11)
   dedupe keys (see data-model.md); changed fields → change_log;
   last_verified_at refreshed only for re-verified fields
   ↓
PROGRESS WRITER — research_jobs.progress updates every phase transition
```

## Depth level profiles (config/depth_profiles.py)

| Param | L1 | L2 | L3 |
|---|---|---|---|
| search_pages_max | 3 | 6 | 10 |
| sitemap_harvest | portals_only | all_universities | full_sitemaps |
| domain_page_cap | 15 | 40 | 100 |
| registry_sources | national_only | national+ror | national+ror+eter |

## Idempotency rules

- Re-runs never duplicate: upsert on natural keys.
- CLOSED items are updated in place (status), never deleted.
- change_log written only when value actually changes.
- Job resume not supported v1; failed jobs restart from scratch (documented).

## Local usage

```powershell
cd apps/agent
uv sync
uv run agent doctor                # env key presence check
uv run agent countries             # seeded country list
uv run agent run --countries IT --depth L1 --dry-run   # plan without writes/crawl cost
uv run agent run --countries IT --depth L2             # real run, writes staging DB
```
