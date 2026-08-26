-- EuropaGrad initial schema (task 2)
-- Source of truth: docs/data-model.md
-- Apply via: Supabase Dashboard SQL Editor, or `supabase db push`, or the setup script.

-- ============ ENUMS ============
create type funding_class as enum ('FULLY_FUNDED','FULLY_FUNDED_STIPEND','TUITION_FREE','TUITION_WAIVER','PARTIAL_SCHOLARSHIP','LOW_TUITION','SELF_FUNDED','RESEARCH_FUNDED','ASSISTANTSHIP','NOT_SPECIFIED');
create type opportunity_type as enum ('GOVERNMENT_SCHOLARSHIP','UNIVERSITY_SCHOLARSHIP','EXTERNAL_SCHOLARSHIP','EU_SCHEME','JOINT_MULTI_COUNTRY');
create type source_tier as enum ('TIER1_OFFICIAL','TIER2_PORTAL','TIER3_COMMUNITY');
create type match_class as enum ('HIGH','POSSIBLE','LOW','UNKNOWN');
create type scholarship_match as enum ('STRONG','POSSIBLE','WEAK','NOT_ELIGIBLE','UNKNOWN');
create type deadline_status as enum ('OPEN','APPROACHING','NOT_YET_OPEN','FUTURE_NOT_PUBLISHED','CLOSED','UNKNOWN');
create type job_status as enum ('PENDING','RUNNING','DONE','FAILED','CANCELLED');
create type tracker_status as enum ('INTERESTED','RESEARCHING','SHORTLISTED','APPLIED','SCHOLARSHIP_APPLIED','ADMISSION_RECEIVED','ACCEPTED','REJECTED');

-- ============ DATASET TABLES (public read, agent-only write via service role) ============

create table countries (
  id text primary key,                -- ISO2 code
  name text not null unique,
  region text not null check (region in ('EU','EFTA','OTHER')),
  is_launch_seed boolean not null default false,
  pack jsonb not null default '{}'::jsonb,
  evidence jsonb not null default '[]'::jsonb
);

create table universities (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  country_id text not null references countries(id),
  city text,
  website text,
  registry_ids jsonb not null default '{}'::jsonb,   -- {ror, eter, national}
  type text check (type in ('PUBLIC','PRIVATE')),
  created_at timestamptz not null default now()
);

create unique index universities_country_name_key on universities(country_id, lower(name));

create table programs (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references universities(id) on delete cascade,
  name text not null,
  degree text,
  field_tags text[] not null default '{}',
  language text,
  duration_months integer,
  intakes jsonb not null default '[]'::jsonb,        -- [{name, start_date}]
  tuition_eur_per_year numeric,
  other_fees jsonb,
  funding_class funding_class not null default 'NOT_SPECIFIED',
  ielts jsonb,                                        -- {overall, min_band} | null
  toefl jsonb,
  moi_policy text check (moi_policy in ('ACCEPTED','CONDITIONAL','NOT_ACCEPTED','NOT_SPECIFIED')) default 'NOT_SPECIFIED',
  gpa_req text,
  prerequisites text[] not null default '{}',
  application_fee_eur numeric,
  program_deadline date,
  scholarship_deadline date,
  deadline_status deadline_status not null default 'UNKNOWN',
  part_time_info text,
  is_joint_program boolean not null default false,
  partner_universities text[] not null default '{}',
  mobility_countries text[] not null default '{}',
  links jsonb not null default '{}'::jsonb,           -- {program, admissions, scholarships, government}
  match_hints jsonb,
  last_verified_at timestamptz,
  evidence jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create unique index programs_dedupe_key on programs(university_id, lower(name), coalesce(program_deadline, '1900-01-01'::date));

create table scholarships (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  provider_type opportunity_type not null,
  provider_name text,
  countries_supported text[] not null default '{}',
  fields_eligible text[],
  nationality_list text[],
  bangladesh_eligible boolean,                        -- null = unknown
  amount jsonb not null default '{}'::jsonb,          -- {tuition, stipend_monthly, accommodation, travel, insurance}
  gpa_min numeric,
  age_max integer,
  requires_admission_first boolean,
  separate_application boolean,
  competitiveness_note text,
  deadline date,
  deadline_status deadline_status not null default 'UNKNOWN',
  links jsonb not null default '{}'::jsonb,
  last_verified_at timestamptz,
  evidence jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table program_scholarships (
  program_id uuid not null references programs(id) on delete cascade,
  scholarship_id uuid not null references scholarships(id) on delete cascade,
  applicability_note text,
  verified boolean not null default false,
  primary key (program_id, scholarship_id)
);

create table sources (
  id uuid primary key default gen_random_uuid(),
  url text not null unique,
  title text,
  tier source_tier not null default 'TIER2_PORTAL',
  retrieved_at timestamptz not null default now()
);

create table change_log (
  id bigint generated always as identity primary key,
  entity_type text not null,
  entity_id uuid not null,
  field text not null,
  old_value jsonb,
  new_value jsonb,
  source_id uuid references sources(id),
  changed_at timestamptz not null default now()
);

-- ============ USER TABLES (owner-only via RLS) ============

create table user_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  bachelor_degree text,
  major text,
  cgpa numeric,
  graduation_year integer,
  tests jsonb,                                        -- {ielts: {overall, bands}, toefl} | null
  moi_available boolean,
  preferences jsonb not null default '{}'::jsonb,     -- {weights, default_filters, regions}
  updated_at timestamptz not null default now()
);

create table saved_items (
  user_id uuid not null references auth.users(id) on delete cascade,
  entity_type text not null check (entity_type in ('PROGRAM','SCHOLARSHIP')),
  entity_id uuid not null,
  note text,
  created_at timestamptz not null default now(),
  primary key (user_id, entity_type, entity_id)
);

create table tracker_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  program_id uuid not null references programs(id) on delete cascade,
  status tracker_status not null default 'INTERESTED',
  deadline_reminder_date date,
  notes jsonb not null default '{}'::jsonb,           -- per-status timestamps
  updated_at timestamptz not null default now(),
  unique (user_id, program_id)
);

create table search_presets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  filters jsonb not null,
  weights jsonb,
  alert_enabled boolean not null default false,
  created_at timestamptz not null default now(),
  unique (user_id, name)
);

-- ============ OPERATIONS TABLES ============

create table research_jobs (
  id uuid primary key default gen_random_uuid(),
  triggered_by uuid references auth.users(id) on delete set null,  -- null = system/schedule
  countries text[] not null,
  depth_level text not null default 'L2' check (depth_level in ('L1','L2','L3')),
  status job_status not null default 'PENDING',
  progress jsonb not null default '{}'::jsonb,        -- {phase, universities_done, universities_total, pages_crawled, extracted}
  error text,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create table domain_fetch_stats (
  domain text primary key,
  best_engine text check (best_engine in ('STATIC','PLAYWRIGHT','CRAWL4AI')),
  static_failures integer not null default 0,
  playwright_failures integer not null default 0,
  last_success timestamptz
);

-- ============ INDEXES ============

create index programs_country_idx on programs(university_id);
create index programs_funding_idx on programs(funding_class);
create index programs_deadline_status_idx on programs(deadline_status);
create index programs_joint_idx on programs(is_joint_program) where is_joint_program;
create index programs_field_tags_idx on programs using gin(field_tags);
create index programs_deadline_idx on programs(program_deadline);
create index universities_country_idx on universities(country_id);
create index scholarships_bd_idx on scholarships(bangladesh_eligible) where bangladesh_eligible is true;
create index scholarships_provider_idx on scholarships(provider_type);
create index tracker_user_idx on tracker_entries(user_id);
create index saved_user_idx on saved_items(user_id);
create index change_entity_idx on change_log(entity_type, entity_id);
create index research_jobs_status_idx on research_jobs(status);
create index sources_url_idx on sources(url);

-- ============ ROW LEVEL SECURITY ============

alter table countries enable row level security;
alter table universities enable row level security;
alter table programs enable row level security;
alter table scholarships enable row level security;
alter table program_scholarships enable row level security;
alter table sources enable row level security;
alter table change_log enable row level security;
alter table user_profiles enable row level security;
alter table saved_items enable row level security;
alter table tracker_entries enable row level security;
alter table search_presets enable row level security;
alter table research_jobs enable row level security;
alter table domain_fetch_stats enable row level security;

-- Public read on dataset
create policy "dataset_public_read_countries" on countries for select using (true);
create policy "dataset_public_read_universities" on universities for select using (true);
create policy "dataset_public_read_programs" on programs for select using (true);
create policy "dataset_public_read_scholarships" on scholarships for select using (true);
create policy "dataset_public_read_crossmatch" on program_scholarships for select using (true);
create policy "dataset_public_read_sources" on sources for select using (true);
create policy "dataset_public_read_change_log" on change_log for select using (true);

-- Owner-only user tables (writes go through policies; service role bypasses RLS)
create policy "profiles_owner_all" on user_profiles for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "saved_items_owner_all" on saved_items for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "tracker_owner_all" on tracker_entries for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "presets_owner_all" on search_presets for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- research_jobs: users see + create own; agent (service role) updates unrestricted
create policy "jobs_owner_select" on research_jobs for select using (auth.uid() = triggered_by or triggered_by is null);
create policy "jobs_owner_insert" on research_jobs for insert with check (auth.uid() = triggered_by);

-- domain_fetch_stats: no policies => only service role accesses it

-- ============ SEED: 30 European countries + US/AU extras ============

insert into countries (id, name, region, is_launch_seed) values
  ('AT','Austria','EU',false),
  ('BE','Belgium','EU',false),
  ('BG','Bulgaria','EU',false),
  ('CH','Switzerland','EFTA',false),
  ('CY','Cyprus','EU',false),
  ('CZ','Czechia','EU',false),
  ('DE','Germany','EU',true),
  ('DK','Denmark','EU',false),
  ('EE','Estonia','EU',false),
  ('ES','Spain','EU',false),
  ('FI','Finland','EU',false),
  ('FR','France','EU',true),
  ('GR','Greece','EU',false),
  ('HR','Croatia','EU',false),
  ('HU','Hungary','EU',false),
  ('IE','Ireland','EU',false),
  ('IS','Iceland','EFTA',false),
  ('IT','Italy','EU',true),
  ('LT','Lithuania','EU',false),
  ('LU','Luxembourg','EU',false),
  ('LV','Latvia','EU',false),
  ('MT','Malta','EU',false),
  ('NL','Netherlands','EU',true),
  ('NO','Norway','EFTA',false),
  ('PL','Poland','EU',false),
  ('PT','Portugal','EU',false),
  ('RO','Romania','EU',false),
  ('SE','Sweden','EU',true),
  ('SI','Slovenia','EU',false),
  ('SK','Slovakia','EU',false),
  ('US','United States','OTHER',false),
  ('AU','Australia','OTHER',false)
on conflict (id) do nothing;
