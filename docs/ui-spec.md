# UI Spec

Design direction: clean academic tool — generous whitespace, strong typographic hierarchy, indigo primary (#4338ca) + emerald accent (#059669), neutral slate surfaces, 8pt spacing grid, Inter/system font stack. Mobile-first responsive (360px → 1440px). Dark mode via CSS vars from day one.

## Route map (src/app)

| Route | Screen | Notes |
|---|---|---|
| / | Landing + Search configurator entry | hero, value props, quick country picker |
| /search | Search configurator | modes A-D, profile form, filters, weight sliders, depth selector, triggers search/research |
| /results | Results table | rank rows, sticky header, sort/filter chips, status badges, score tooltip |
| /programs/[id] | Program detail | full field sheet + evidence table + linked scholarships + change history |
| /scholarships/[id] | Scholarship detail | eligibility matrix + cross-matched programs |
| /countries/[code] | Country guide | pack data: system, costs, work rules, timeline |
| /erasmus | Joint/multi-country section | dedicated listing |
| /compare | Side-by-side comparison | ≤4 entities |
| /plan | My Plan | shortlist + tracker board (auth-gated) |
| /report | Generated report view | exec summary → strategy groups → sources, print-to-PDF styles |
| /auth/callback | OAuth/magic-link handler | |

## Component inventory (shadcn/ui primitives used)

table, card, badge, button, input, label, select, slider, checkbox, switch, tabs, dialog, sheet (mobile nav + progress drawer), tooltip, dropdown-menu, separator, skeleton, toast/sonner, command (search palette P1), form (react-hook-form later if needed).

Custom feature components (apps/web/src/components/): results-table.tsx, filters-panel.tsx, weights-editor.tsx, profile-form.tsx, evidence-table.tsx, deadline-badge.tsx, match-pill.tsx, funding-tag.tsx, job-progress-drawer.tsx, export-dialog.tsx, tracker-board.tsx, country-pack-card.tsx.

## Required states (every screen)

Loading (skeletons matching layout) · Empty ("no results — widen filters" + one-click reset) · Error (retry action) · Research-in-progress (drawer with live phase log). Forms: inline validation messages, disabled-submit while pending, success feedback.

## Mock-data contracts (used by generated UI until DB wiring)

```ts
type FundingClass = 'FULLY_FUNDED'|'FULLY_FUNDED_STIPEND'|'TUITION_FREE'|'TUITION_WAIVER'|'PARTIAL_SCHOLARSHIP'|'LOW_TUITION'|'SELF_FUNDED'|'RESEARCH_FUNDED'|'ASSISTANTSHIP'|'NOT_SPECIFIED';
type DeadlineStatus = 'OPEN'|'APPROACHING'|'NOT_YET_OPEN'|'FUTURE_NOT_PUBLISHED'|'CLOSED'|'UNKNOWN';
type MatchClass = 'HIGH'|'POSSIBLE'|'LOW'|'UNKNOWN';

interface ProgramRow {
  id: string; rank?: number;
  country: string; city: string; university: string;
  program: string; degree: string; fieldTags: string[];
  language: string; durationMonths: number;
  tuitionEurPerYear: number | null;
  fundingClass: FundingClass; scholarshipName: string | null;
  ieltsOverall: number | null; moiAccepted: boolean | 'NOT_SPECIFIED';
  intake: string; deadline: string | null; deadlineStatus: DeadlineStatus; daysRemaining: number | null;
  partTimeWork: 'ALLOWED'|'RESTRICTED'|'NOT_ALLOWED'|'NOT_SPECIFIED';
  matchClass: MatchClass; score: number; // 0-100
  isJointProgram: boolean;
}

interface EvidenceEntry { field: string; value: string; sourceUrl: string; sourceTier: 'TIER1_OFFICIAL'|'TIER2_PORTAL'|'TIER3_COMMUNITY'; quote: string; retrievedAt: string; }

interface FiltersState {
  countries: string[]; fields: string[]; mode: 'SINGLE'|'MULTI'|'EUROPE'|'BEST_FOR_ME';
  fundingClasses: FundingClass[]; moiOnly: boolean; noIelts: boolean;
  partTimeImportance: 'REQUIRED'|'PREFERRED'|'IGNORED';
  intakeWindow: 'NEXT'|'NEXT_YEAR'|'SPECIFIC'|'ANY'; intakeYear?: number;
  jointProgramsOnly: boolean; depthLevel: 'L1'|'L2'|'L3';
}
```

## Integrating externally generated UI (v0 etc.)

Procedure lives in the `ui-drop-in` skill (.kilo/skills/ui-drop-in/SKILL.md). Summary: generate screen-by-screen with the master prompt (kept in docs/state.md decisions log), drop files at the paths above, add missing shadcn primitives via `pnpm dlx shadcn@latest add`, replace mock modules with these types, strip vendor boilerplate, verify lint/typecheck/responsive/a11y.
