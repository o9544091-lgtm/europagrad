# Project State

**Phase:** 0-1 Foundation — scaffold complete (task 1 ☑), awaiting Supabase project (task 2).
**Last updated:** 2026-08-25

## Decisions log

| # | Decision | Rationale |
|---|---|---|
| D1 | Live on-demand research runs + shared Postgres cache (not pure curated, not per-search live crawl) | User chose live agent; cache-first variant keeps instant UX while compounding coverage across users |
| D2 | Python agent (Scrapy core, httpx static, Playwright escalation, Crawl4AI optional) | Deep-crawl ecosystem strongest in Python; $0 runtime via GitHub Actions; user preference |
| D3 | Adaptive per-domain engine routing w/ memory (`domain_fetch_stats`), not fixed chain | Browser-first is 10-50× slower at thousands of pages/domain scale; escalation only where needed |
| D4 | Discovery = official registries (ROR/ETER/national) + sitemap harvest + Tavily paginated search | Satisfies "visit every university" reliably without brute-force crawling |
| D5 | Depth levels L1/L2/L3 user-selectable | User requested "level scaling"; caps time/cost predictably |
| D6 | Supabase replaces Firebase (firebase MCP removed from .kilo/kilo.json) | Relational data + heavy filtering favors Postgres; user approved "whatever suits better" |
| D7 | Hosting: Vercel (web) + Supabase free (DB/auth/realtime) + GitHub Actions (agent) | All free tiers; long crawls don't fit serverless timeouts |
| D8 | Contract TS↔Python = Postgres migrations + Pydantic JSON Schemas | Single source of truth; CI drift check prevents enum divergence |
| D9 | UI generated externally in a full-app tool (Lovable / Manus.im recommended; v0 works too), downloaded as files/ZIP, absorbed via `ui-drop-in` skill | User workflow preference: visual iteration first, then drop into repo. Prompt targets React SPA output (what those tools do best); conversion to Next.js App Router is mechanical — see skill |
| D10 | WebReaper rejected | Unmaintained; capability covered by Scrapy+Playwright+Crawl4AI |
| D11 | External UI drop-in completed: Manus-generated SPA (`eurofund-masters-explorer`) absorbed into Next.js App Router per ui-drop-in skill | User generated full UI externally as planned (D9); all 10 screens + shell now presentational on mock data; verified lint/typecheck/tests/build + browser spot-checks desktop & 360px |

### Drop-in deviations (from the generated original)

- Rebrand: "EuroFund Masters Explorer" → "EuropaGrad" (logo mark = "EG" monogram; vendor PNG/logo images not shipped in download, replaced with styled marks + gradients)
- wouter → next/link + next/navigation (usePathname/useRouter); param pages (`/programs/[id]`, `/scholarships/[id]`, `/countries/[code]`) take params via server-wrapper props
- Vendored shadcn `ui/input.tsx` replaced with standard shadcn input (original dragged in template Dialog + custom hooks); 11 primitives vendored as-is (button, card, checkbox, dropdown-menu, input, label, select, skeleton, switch, tabs, tooltip)
- Discarded: ManusDialog, Map.tsx (unused), ThemeContext (never mounted — dark is default via `html.dark`), const.ts OAuth boilerplate, server/, shared/, hooks (useComposition/usePersistFn/useMobile), next-themes
- Added deps: sonner, tw-animate-css, 8 @radix-ui packages; Toaster mounted in providers.tsx (TooltipProvider + ErrorBoundary + Toaster)
- Dark "Nocturne Ledger" theme adopted wholesale into globals.css (replaces original placeholder palette); Google Fonts Inter via CSS @import (swap to next/font later)
- Mock data/types kept verbatim — they match the canonical contract in docs/ui-spec.md

## Current status

- Tasks 1-11 done, task 12 in verification. Repo LIVE: github.com/o9544091-lgtm/europagrad (secrets set: SUPABASE_URL, SUPABASE_SERVICE_KEY, DATABASE_URL). Keyless operation proven: heuristic extractor + DDG search = real runs work without API keys; quality auto-upgrades when OPENROUTER_API_KEY/TAVILY_API_KEY land. Recommended model: google/gemini-2.0-flash-001 (~cents per L1 run); free alt: deepseek/deepseek-chat-v3-0324:free. All prior completions (tasks 1-11) unchanged.
- Auth facts: Email provider default-on; magic-link OTP accepted live (free-tier rate limit ~2 sends/hour — expected). Google button shows explanatory toast until OAuth client ID/secret are added in Dashboard → Authentication → Providers → Google. RLS verified at SQL level (11 tests) and API level (8 tests). Test scripts: `scripts/test-rls.mjs`, `apps/web/scripts/auth-e2e.mjs`.
- Supabase connection facts (no secrets here — credentials live in gitignored env files only): project ref `zlcyhizyplmthbznjfny`, pooler region `aws-0-ap-southeast-1`. Env files populated: `apps/web/.env.local`, `apps/agent/.env`.
- Tools: `scripts/apply-migration.mjs`, `scripts/check-taxonomy-drift.mjs`, `scripts/test-rls.mjs`, `apps/web/scripts/auth-e2e.mjs` (all read env via `node --env-file=apps/agent/.env`).
- Web validation green: lint, typecheck, tests, build. Agent: 5/5 pytest, ruff clean.
- Toolchain installed: pnpm 9.15.0, uv 0.12.5.
- Repo not yet git-initialized/pushed — when pushed, add `DATABASE_URL` as a GitHub Actions secret so the CI drift check activates.

## Next actions

1. Tasks 6-8: agent pipeline engines — static fetch tier, Playwright/Crawl4AI escalation + adaptive router, registry ingestion + sitemap harvester (fixture-based; unblocked).
2. User (whenever convenient): add Google OAuth credentials in Supabase Dashboard; also verify Site URL / redirect URLs include localhost:3000 (default) and later the Vercel domain.
3. Tasks 14-21: wire the existing UI screens to Supabase data.

## Known bugs

- None in product code.
- Harness quirk (non-blocking): this Kilo session's config-validation hook reports `Failed to parse frontmatter` for every `.kilo/command/*.md`, even byte-identical copies of working global commands (`~/.config/kilo/command/graphify.md`). Files match the documented format and load normally via the standard command parser on restart. Skills under `.kilo/skills/` validate clean.

## Appendix — Master prompt for external UI generation (Lovable / Manus.im / v0)

Paste everything inside the fence as the FIRST message. Then iterate visually on any screen — design changes are safe; ask only that types/props stay intact. When satisfied, download files/ZIP and follow `.kilo/skills/ui-drop-in/SKILL.md`.

````markdown
Build a complete, polished, production-quality front-end prototype of EuropaGrad — a web app that helps Bangladeshi CSE students discover, filter, rank, track, and export funded European Master's programs and scholarships, where every fact is traced to an official source.

## Tech rules (strict)

- React + TypeScript (strict mode, no `any`) + Tailwind CSS + shadcn/ui components + lucide-react icons only
- Client-side SPA with routes: `/`, `/search`, `/results`, `/programs/:id`, `/scholarships/:id`, `/countries/:code`, `/erasmus`, `/compare`, `/plan`, `/report`
- STRICTLY presentational: no authentication, no database, no API calls, no server code, no env vars, no analytics/tracking scripts, no payment/contact forms that send anywhere
- ALL data comes from two modules you create: `src/lib/types.ts` (exact types below) and `src/lib/mock-data.ts`
- Keep each screen as its own file (src/pages/…) and reusable feature components under `src/components/` — never one monolithic file
- No TODO comments, no lorem ipsum

## Shared types — implement exactly (these mirror our production database)

```ts
export type FundingClass = 'FULLY_FUNDED' | 'FULLY_FUNDED_STIPEND' | 'TUITION_FREE' | 'TUITION_WAIVER' | 'PARTIAL_SCHOLARSHIP' | 'LOW_TUITION' | 'SELF_FUNDED' | 'RESEARCH_FUNDED' | 'ASSISTANTSHIP' | 'NOT_SPECIFIED';
export type DeadlineStatus = 'OPEN' | 'APPROACHING' | 'NOT_YET_OPEN' | 'FUTURE_NOT_PUBLISHED' | 'CLOSED' | 'UNKNOWN';
export type MatchClass = 'HIGH' | 'POSSIBLE' | 'LOW' | 'UNKNOWN';
export type PartTimeWork = 'ALLOWED' | 'RESTRICTED' | 'NOT_ALLOWED' | 'NOT_SPECIFIED';
export type SourceTier = 'TIER1_OFFICIAL' | 'TIER2_PORTAL' | 'TIER3_COMMUNITY';

export interface ProgramRow {
  id: string; rank?: number;
  country: string; city: string; university: string;
  program: string; degree: string; fieldTags: string[];
  language: string; durationMonths: number;
  tuitionEurPerYear: number | null;
  fundingClass: FundingClass; scholarshipName: string | null;
  ieltsOverall: number | null; moiAccepted: boolean | 'NOT_SPECIFIED';
  intake: string; deadline: string | null; deadlineStatus: DeadlineStatus; daysRemaining: number | null;
  partTimeWork: PartTimeWork;
  matchClass: MatchClass; score: number; // 0-100
  isJointProgram: boolean;
}

export interface Scholarship {
  id: string; name: string; providerName: string;
  providerType: 'GOVERNMENT_SCHOLARSHIP' | 'UNIVERSITY_SCHOLARSHIP' | 'EXTERNAL_SCHOLARSHIP' | 'EU_SCHEME' | 'JOINT_MULTI_COUNTRY';
  bangladeshEligible: boolean | 'UNKNOWN';
  amountSummary: string; stipendMonthlyEur: number | null;
  requiresAdmissionFirst: boolean; separateApplication: boolean;
  competitivenessNote: string;
  deadline: string | null; deadlineStatus: DeadlineStatus;
}

export interface EvidenceEntry {
  field: string; value: string; sourceUrl: string; sourceTier: SourceTier;
  quote: string; retrievedAt: string;
}

export interface CountryPack {
  code: string; name: string; flagEmoji: string;
  tuitionNorms: string; livingCostMonthlyEur: { low: number; avg: number };
  partTimeRules: string; visaNotes: string;
  majorScholarships: string[]; applicationPlatform: string;
  englishTaughtAvailability: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface FiltersState {
  countries: string[]; fields: string[]; mode: 'SINGLE' | 'MULTI' | 'EUROPE' | 'BEST_FOR_ME';
  fundingClasses: FundingClass[]; moiOnly: boolean; noIelts: boolean;
  partTimeImportance: 'REQUIRED' | 'PREFERRED' | 'IGNORED';
  intakeWindow: 'NEXT' | 'NEXT_YEAR' | 'SPECIFIC' | 'ANY'; intakeYear?: number;
  jointProgramsOnly: boolean; depthLevel: 'L1' | 'L2' | 'L3';
}
```

## Mock data requirements

- ≥20 programs across Germany, Italy, France, Netherlands, Sweden using realistic institutions (e.g., TU Berlin, RWTH Aachen, Politecnico di Milano, University of Bologna, Université Paris-Saclay, TU Delft, KTH Stockholm, University of Helsinki) with plausible-but-clearly-sample values
- Cover ALL FundingClass values at least once, and all six DeadlineStatus values (include CLOSED and FUTURE_NOT_PUBLISHED examples), plus 2–3 isJointProgram entries (Erasmus Mundus style, multiple mobility countries)
- ≥8 scholarships (DAAD EPOS, Invest Your Talent in Italy, Eiffel, Erasmus Mundus CATO/CNV-style, Holland Scholarship, Swedish Institute, etc.) with realistic eligibility notes
- Country packs for the five seed countries; evidence entries whose quotes look like real requirement sentences, with sourceUrl values pointing at plausible official domains — visibly labeled "sample data for prototype"

## Design system

- Clean academic-tool aesthetic: generous whitespace, strong typographic hierarchy, 8pt spacing grid, Inter font, tabular numerals in tables
- Colors: slate neutrals; primary indigo #4338ca; accent emerald #059669; destructive #dc2626. Full dark mode with a toggle, CSS-variable driven
- Status color semantics everywhere: OPEN emerald · APPROACHING amber · NOT_YET_OPEN blue · CLOSED muted red · FUTURE_NOT_PUBLISHED slate outline · UNKNOWN gray outline
- Mobile-first responsive 360px→1440px; data tables collapse to stacked cards below 768px
- Accessibility: WCAG AA contrast, visible focus rings, aria-labels on icon buttons, full keyboard navigation

## Screens — build ALL ten

1. **Landing (/)**: hero "Find your funded Master's in Europe", subline about evidence-cited data; three value props (every fact sourced & dated, MOI/no-IELTS filtering, deadline intelligence); prominent quick-picks for Germany, Italy, France, Netherlands, Sweden + "All Europe"; CTA to /search; how-it-works strip (search → verify sources → track deadlines)
2. **Search (/search)**: mode selector (Single country / Multiple countries / All Europe / Best countries for me); academic profile form (bachelor major select, CGPA input 0–4 scale, graduation year, IELTS score input OR "I have MOI letter" toggle); filter groups (funding checkboxes, language chips, part-time importance radio, intake window); weight sliders (funding, academic match, tuition, language, living cost, part-time, deadline) showing percentages that normalize to 100% with a live balance bar; depth level cards L1 Quick (~minutes) / L2 Standard (~1–2h) / L3 Exhaustive (~hours); sticky submit button
3. **Results (/results)**: sticky-header sortable table with columns Rank · Country · University · Program (+joint badge) · Funding tag · Tuition €/yr · Scholarship · IELTS/MOI chip · Intake · Deadline (+status badge +days remaining) · Part-time · Match pill · Score (hover tooltip breaking down subscores); active-filter chips row above with individual remove ×; column visibility dropdown; row click navigates to program detail; export dropdown (XLSX/CSV/JSON); result count header; empty state with "widen filters" reset CTA; skeleton rows while loading
4. **Program detail (/programs/:id)**: breadcrumb; header card (university, program, city/country, score ring, Add-to-plan button); info sheet grouped in tabs/sections: Academic (degree, duration, field tags, GPA reqs, prerequisites), Funding (class badge, tuition, fees, linked scholarship cards), Language (IELTS overall + band, TOEFL, MOI policy callout), Deadlines (program vs scholarship deadlines side-by-side, status badges, days remaining), Work (part-time policy + legal note), Links (official buttons: Program page, Admissions, Scholarships, Government portal — external-link icons); Evidence table listing EvidenceEntry rows (field, value, quote in styled blockquote, tier badge, source link, retrieved date); amber conflict-warning banner component shown on one sample program; slate "needs re-verification" staleness banner on another; change-history mini-timeline (old value → new value, date)
5. **Scholarship detail (/scholarships/:id)**: provider header, benefit breakdown grid (tuition/stipend/accommodation/travel/insurance), eligibility matrix checklist (nationality BD ✓/✗/unknown, field, GPA, age, admission-first, separate application), cross-matched programs list linking to program details, deadline card, evidence table
6. **Country guide (/countries/:code)**: pack hero (flag, name, English-taught availability meter); stat tiles (tuition norms, living cost low/avg, part-time rules summary); scholarship ecosystem list; application platform + timeline notes; top programs in country (mini-table reusing row styles)
7. **Erasmus (/erasmus)**: explainer banner (what joint/multi-country degrees are); dedicated table of joint programs with partner-university avatars/chips and mobility-country flags; filter toggle "fully funded only"
8. **Compare (/compare)**: select up to 4 entities; side-by-side column comparison across funding, tuition, stipend, language/MOI, deadlines, part-time, living cost, match, score; highlight-best-per-row styling; remove-entity controls
9. **My Plan (/plan)**: two panes — left: shortlist cards (saved programs w/ next-deadline highlight); right: tracker kanban with columns Interested → Researching → Shortlisted → Applied → Scholarship Applied → Result; draggable-looking cards (visual only ok), each card showing days-to-deadline chip; sign-in prompt banner explaining saving requires a free account
10. **Report (/report)**: generated-report layout: executive summary paragraph auto-assembled from mock data; grouped lists (Best fully funded, Best tuition-free, Best without IELTS, Best accepting MOI); upcoming deadlines table sorted by date; Reach/Target/Safety strategy board; sources appendix (numbered, tiered); print-friendly button; subtle "generated from sample data" watermark

## Quality bar

- Loading skeleton states on /results and all detail pages; error banner with Retry on report
- Every icon button has an aria-label; modals/sheets close on Esc; focus trapped in dialogs
- No dead links: internal nav works between all ten screens; external links use real-looking URLs with target=_blank
- Consistent empty states with one-click recovery actions
````

After download: run the `ui-drop-in` skill procedure — SPA pages convert to Next.js App Router by wrapping each screen in a `"use client"` page component at the route paths in docs/ui-spec.md; swap `react-router` Link/useNavigate for `next/link`/`useRouter`; keep types verbatim.
