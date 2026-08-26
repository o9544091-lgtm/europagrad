---
name: data-integrity
description: Anti-hallucination data rules for EuropaGrad. Load whenever editing agent extraction/storage code, pipeline QC, or any UI that displays program/scholarship facts.
---

# Data Integrity Rules (EuropaGrad)

Load this skill before touching anything that extracts, stores, transforms, or displays research data.

## Non-negotiables

1. **Citation pairs are mandatory.** Every critical field value must carry `{source_url, quote}` where quote is a verbatim substring of fetched content (validated at ≥0.95 similarity). No pair ⇒ value becomes `NOT_SPECIFIED`. Never store an uncited value.
2. **Absence is not evidence.** "Not specified on official source" must never be interpreted, displayed, or stored as "not required".
3. **Funding taxonomy precision.** FULLY_FUNDED ≠ TUITION_FREE ≠ TUITION_WAIVER ≠ PARTIAL_SCHOLARSHIP ≠ LOW_TUITION. Never map between them implicitly. Label `FULLY_FUNDED` only when evidence covers tuition AND the source states the coverage scope.
4. **Two deadline tracks.** Program application deadline and scholarship deadline are separate fields. Never merge. CLOSED items update status in place — never delete.
5. **Conflict handling.** When sources disagree: keep all versions with tiers + dates, set conflict flag, prefer newest Tier-1 in display. Never silently pick one when it materially affects eligibility.
6. **Tier precedence.** TIER1_OFFICIAL (gov > university > scholarship org > EU org) beats TIER2_PORTAL beats TIER3_COMMUNITY. Tier-3 may inspire discovery; it never overrides official sources for stored facts.
7. **Match language.** Eligibility outputs say "Likely eligible based on published requirements". Never "you are eligible/admitted".
8. **Freshness.** `last_verified_at` updates only for re-verified fields. >90 days ⇒ stale badge. Refresh diffs write change_log rows — old values preserved.

## Review checklist (run before merging changes to extraction/storage/display)

- [ ] New fields added to schemas? Citation requirement enforced there too?
- [ ] Any place rendering a fact without its evidence link?
- [ ] Any string literal duplicating enum values instead of importing taxonomy? (TS types generated from DB; Python mirrors Pydantic — fix at source, don't fork.)
- [ ] Tests updated: golden fixtures for new extraction rules, including a no-quote rejection case?
- [ ] Does any code path treat null/NOT_SPECIFIED as a positive eligibility signal?

## When you cannot comply

If a task seems to require guessing or fabricating a value (e.g., demo data for a screen), use clearly-labeled mock fixtures (`src/lib/mock-data.ts` pattern) confined to presentation code — never write fabricated values into storage code paths, migrations, seeds of real tables, or documentation as if factual.
