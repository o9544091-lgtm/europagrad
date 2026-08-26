# Data Model (Supabase Postgres)

Status: DRAFT — implemented by task 2. This file is the human-readable contract; migrations are authoritative once written.

## Enums (Postgres — single source of truth)

```sql
CREATE TYPE funding_class AS ENUM ('FULLY_FUNDED','FULLY_FUNDED_STIPEND','TUITION_FREE','TUITION_WAIVER','PARTIAL_SCHOLARSHIP','LOW_TUITION','SELF_FUNDED','RESEARCH_FUNDED','ASSISTANTSHIP','NOT_SPECIFIED');
CREATE TYPE opportunity_type AS ENUM ('GOVERNMENT_SCHOLARSHIP','UNIVERSITY_SCHOLARSHIP','EXTERNAL_SCHOLARSHIP','EU_SCHEME','JOINT_MULTI_COUNTRY');
CREATE TYPE source_tier AS ENUM ('TIER1_OFFICIAL','TIER2_PORTAL','TIER3_COMMUNITY');
CREATE TYPE match_class AS ENUM ('HIGH','POSSIBLE','LOW','UNKNOWN');
CREATE TYPE scholarship_match AS ENUM ('STRONG','POSSIBLE','WEAK','NOT_ELIGIBLE','UNKNOWN');
CREATE TYPE deadline_status AS ENUM ('OPEN','APPROACHING','NOT_YET_OPEN','FUTURE_NOT_PUBLISHED','CLOSED','UNKNOWN');
CREATE TYPE job_status AS ENUM ('PENDING','RUNNING','DONE','FAILED','CANCELLED');
CREATE TYPE tracker_status AS ENUM ('INTERESTED','RESEARCHING','SHORTLISTED','APPLIED','SCHOLARSHIP_APPLIED','ADMISSION_RECEIVED','ACCEPTED','REJECTED');
```

## Tables

**countries**: id (iso2 pk), name, region (EU/EFTA/OTHER), is_launch_seed bool, pack jsonb (education system, tuition norms, work rules, visa basics, living-cost baseline monthly EUR {low,avg,city_breakdown}, major portals[], application platform, timeline notes), evidence jsonb[].

**universities**: id uuid pk, name, country_id fk, city, website, registry_ids jsonb (ROR/ETER/national ids), type (PUBLIC/PRIVATE).

**programs**: id uuid pk, university_id fk, name, degree (MSc/MA/...), field_tags text[] (cs, ai, ml, ds, security, se, it, robotics, hci, embedded, systems, interdisciplinary), language, duration_months int, intakes jsonb [{name, start_date}], tuition_eur_per_year numeric null, other_fees jsonb, funding_class funding_class, ielts jsonb ({overall, min_band} | null), toefl jsonb, moi_policy (ACCEPTED/CONDITIONAL/NOT_ACCEPTED/NOT_SPECIFIED), gpa_req text, prerequisites text[], application_fee_eur numeric, program_deadline date null, scholarship_deadline date null, deadline_status deadline_status, part_time_info text, is_joint_program bool, partner_universities text[], mobility_countries text[], links jsonb ({program, admissions, scholarships, government}), match_hints jsonb, last_verified_at timestamptz, evidence jsonb[]. Unique dedupe key: (university_id, lower(name), intake_year).

**scholarships**: id uuid pk, name, provider_type opportunity_type, provider_name, countries_supported text[], fields_eligible text[] | null (=all), nationality_list text[] | null, bangladesh_eligible bool | unknown, amount jsonb (tuition/stipend_monthly/other benefits), gpa_min numeric, age_max int, requires_admission_first bool, separate_application bool, competitiveness_note text, deadline date null, deadline_status deadline_status, links jsonb, last_verified_at timestamptz, evidence jsonb[].

**program_scholarships**: program_id fk, scholarship_id fk, applicability_note text, verified bool. Cross-match table — a scholarship surfaces for a program ONLY through this join (spec §31).

**sources**: id uuid pk, url unique, title, tier source_tier, retrieved_at.

Evidence entries embed: `{field, value, source_id/url, quote, retrieved_at}`.

**user_profiles**: user_id uuid pk (auth.users fk), bachelor_degree, major, cgpa numeric, graduation_year int, tests jsonb (ielts/toefl scores | null), moi_available bool, preferences jsonb (weights, default filters, regions).

**saved_items**: user_id fk, entity_type (PROGRAM/SCHOLARSHIP), entity_id, note, created_at. PK (user_id, entity_type, entity_id).

**tracker_entries**: id uuid pk, user_id fk, program_id fk, status tracker_status, deadline_reminder_date date null, notes jsonb (per-status timestamps), updated_at.

**research_jobs**: id uuid pk, triggered_by user_id null (null = system/schedule), countries text[], depth_level char(2), status job_status, progress jsonb (phase, universities_done/total, pages_crawled, extracted counts), error text, started_at, finished_at.

**domain_fetch_stats**: domain pk, best_engine (STATIC/PLAYWRIGHT/CRAWL4AI), static_failures int, playwright_failures int, last_success timestamptz.

**change_log**: id bigserial, entity_type, entity_id, field, old_value jsonb, new_value jsonb, source_id fk, changed_at. Written only by agent diff step.

**search_presets**: id uuid, user_id fk, name, filters jsonb, weights jsonb, alert_enabled bool (alerts deferred P2).

## Indexes

programs(country_id), programs(funding_class), programs(deadline_status), programs(is_joint_program) where is_joint_program, programs using gin(field_tags), scholarships(bangladesh_eligible) where true, tracker_entries(user_id), change_log(entity_type, entity_id).

## RLS matrix

| Table | anon | authenticated |
|---|---|---|
| countries/universities/programs/scholarships/program_scholarships/sources/change_log | select | select |
| user_profiles/saved_items/tracker_entries/search_presets | none | all CRUD, user_id = auth.uid() |
| research_jobs | select own | insert own (rate-limited at API), select own |
| domain_fetch_stats | none | none (service role only) |

All writes to dataset tables happen via service role inside the agent only.
