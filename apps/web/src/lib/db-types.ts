export type FundingClass =
  | "FULLY_FUNDED"
  | "FULLY_FUNDED_STIPEND"
  | "TUITION_FREE"
  | "TUITION_WAIVER"
  | "PARTIAL_SCHOLARSHIP"
  | "LOW_TUITION"
  | "SELF_FUNDED"
  | "RESEARCH_FUNDED"
  | "ASSISTANTSHIP"
  | "NOT_SPECIFIED";

export type OpportunityType =
  | "GOVERNMENT_SCHOLARSHIP"
  | "UNIVERSITY_SCHOLARSHIP"
  | "EXTERNAL_SCHOLARSHIP"
  | "EU_SCHEME"
  | "JOINT_MULTI_COUNTRY";

export type SourceTier =
  | "TIER1_OFFICIAL"
  | "TIER2_PORTAL"
  | "TIER3_COMMUNITY";

export type MatchClass = "HIGH" | "POSSIBLE" | "LOW" | "UNKNOWN";

export type ScholarshipMatch =
  | "STRONG"
  | "POSSIBLE"
  | "WEAK"
  | "NOT_ELIGIBLE"
  | "UNKNOWN";

export type DeadlineStatus =
  | "OPEN"
  | "APPROACHING"
  | "NOT_YET_OPEN"
  | "FUTURE_NOT_PUBLISHED"
  | "CLOSED"
  | "UNKNOWN";

export type JobStatus =
  | "PENDING"
  | "RUNNING"
  | "DONE"
  | "FAILED"
  | "CANCELLED";

export type TrackerStatus =
  | "INTERESTED"
  | "RESEARCHING"
  | "SHORTLISTED"
  | "APPLIED"
  | "SCHOLARSHIP_APPLIED"
  | "ADMISSION_RECEIVED"
  | "ACCEPTED"
  | "REJECTED";

export type Region = "EU" | "EFTA" | "OTHER";
export type UniversityType = "PUBLIC" | "PRIVATE";
export type MoiPolicy = "ACCEPTED" | "CONDITIONAL" | "NOT_ACCEPTED" | "NOT_SPECIFIED";
export type DepthLevel = "L1" | "L2" | "L3";
export type SavedEntityType = "PROGRAM" | "SCHOLARSHIP";

export interface CountryRow {
  id: string;
  name: string;
  region: Region;
  is_launch_seed: boolean;
  pack: Record<string, unknown>;
  evidence: unknown[];
}

export interface UniversityRow {
  id: string;
  name: string;
  country_id: string;
  city: string | null;
  website: string | null;
  registry_ids: Record<string, unknown>;
  type: UniversityType | null;
  created_at: string;
}

export interface ProgramRowDb {
  id: string;
  university_id: string;
  name: string;
  degree: string | null;
  field_tags: string[];
  language: string | null;
  duration_months: number | null;
  intakes: { name: string; start_date?: string }[];
  tuition_eur_per_year: string | number | null;
  other_fees: Record<string, unknown> | null;
  funding_class: FundingClass;
  ielts: { overall?: number; min_band?: number } | null;
  toefl: Record<string, unknown> | null;
  moi_policy: MoiPolicy | null;
  gpa_req: string | null;
  prerequisites: string[];
  application_fee_eur: string | number | null;
  program_deadline: string | null;
  scholarship_deadline: string | null;
  deadline_status: DeadlineStatus;
  part_time_info: string | null;
  is_joint_program: boolean;
  partner_universities: string[];
  mobility_countries: string[];
  links: {
    program?: string;
    admissions?: string;
    scholarships?: string;
    government?: string;
  };
  match_hints: Record<string, unknown> | null;
  last_verified_at: string | null;
  evidence: unknown[];
  created_at: string;
}

export interface ScholarshipRow {
  id: string;
  name: string;
  provider_type: OpportunityType;
  provider_name: string | null;
  countries_supported: string[];
  fields_eligible: string[] | null;
  nationality_list: string[] | null;
  bangladesh_eligible: boolean | null;
  amount: Record<string, unknown>;
  gpa_min: string | number | null;
  age_max: number | null;
  requires_admission_first: boolean | null;
  separate_application: boolean | null;
  competitiveness_note: string | null;
  deadline: string | null;
  deadline_status: DeadlineStatus;
  links: Record<string, unknown>;
  last_verified_at: string | null;
  evidence: unknown[];
  created_at: string;
}

export interface ProgramScholarshipRow {
  program_id: string;
  scholarship_id: string;
  applicability_note: string | null;
  verified: boolean;
}

export interface SourceRow {
  id: string;
  url: string;
  title: string | null;
  tier: SourceTier;
  retrieved_at: string;
}

export interface ChangeLogRow {
  id: number;
  entity_type: string;
  entity_id: string;
  field: string;
  old_value: unknown;
  new_value: unknown;
  source_id: string | null;
  changed_at: string;
}

export interface UserProfileRow {
  user_id: string;
  bachelor_degree: string | null;
  major: string | null;
  cgpa: string | number | null;
  graduation_year: number | null;
  tests: Record<string, unknown> | null;
  moi_available: boolean | null;
  preferences: Record<string, unknown>;
  updated_at: string;
}

export interface SavedItemRow {
  user_id: string;
  entity_type: SavedEntityType;
  entity_id: string;
  note: string | null;
  created_at: string;
}

export interface TrackerEntryRow {
  id: string;
  user_id: string;
  program_id: string;
  status: TrackerStatus;
  deadline_reminder_date: string | null;
  notes: Record<string, unknown>;
  updated_at: string;
}

export interface SearchPresetRow {
  id: string;
  user_id: string;
  name: string;
  filters: Record<string, unknown>;
  weights: Record<string, unknown> | null;
  alert_enabled: boolean;
  created_at: string;
}

export interface ResearchJobRow {
  id: string;
  triggered_by: string | null;
  countries: string[];
  depth_level: DepthLevel;
  status: JobStatus;
  progress: Record<string, unknown>;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface DomainFetchStatRow {
  domain: string;
  best_engine: "STATIC" | "PLAYWRIGHT" | "CRAWL4AI" | null;
  static_failures: number;
  playwright_failures: number;
  last_success: string | null;
}
