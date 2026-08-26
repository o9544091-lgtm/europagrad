"""Enum mirrors of Postgres enums (authoritative source: supabase/migrations/0001_init.sql).

Drift against the live database is checked by scripts/check-taxonomy-drift.mjs (task 3).
"""

from enum import StrEnum


class FundingClass(StrEnum):
    FULLY_FUNDED = "FULLY_FUNDED"
    FULLY_FUNDED_STIPEND = "FULLY_FUNDED_STIPEND"
    TUITION_FREE = "TUITION_FREE"
    TUITION_WAIVER = "TUITION_WAIVER"
    PARTIAL_SCHOLARSHIP = "PARTIAL_SCHOLARSHIP"
    LOW_TUITION = "LOW_TUITION"
    SELF_FUNDED = "SELF_FUNDED"
    RESEARCH_FUNDED = "RESEARCH_FUNDED"
    ASSISTANTSHIP = "ASSISTANTSHIP"
    NOT_SPECIFIED = "NOT_SPECIFIED"


class OpportunityType(StrEnum):
    GOVERNMENT_SCHOLARSHIP = "GOVERNMENT_SCHOLARSHIP"
    UNIVERSITY_SCHOLARSHIP = "UNIVERSITY_SCHOLARSHIP"
    EXTERNAL_SCHOLARSHIP = "EXTERNAL_SCHOLARSHIP"
    EU_SCHEME = "EU_SCHEME"
    JOINT_MULTI_COUNTRY = "JOINT_MULTI_COUNTRY"


class SourceTier(StrEnum):
    TIER1_OFFICIAL = "TIER1_OFFICIAL"
    TIER2_PORTAL = "TIER2_PORTAL"
    TIER3_COMMUNITY = "TIER3_COMMUNITY"


class MatchClass(StrEnum):
    HIGH = "HIGH"
    POSSIBLE = "POSSIBLE"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ScholarshipMatch(StrEnum):
    STRONG = "STRONG"
    POSSIBLE = "POSSIBLE"
    WEAK = "WEAK"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    UNKNOWN = "UNKNOWN"


class DeadlineStatus(StrEnum):
    OPEN = "OPEN"
    APPROACHING = "APPROACHING"
    NOT_YET_OPEN = "NOT_YET_OPEN"
    FUTURE_NOT_PUBLISHED = "FUTURE_NOT_PUBLISHED"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TrackerStatus(StrEnum):
    INTERESTED = "INTERESTED"
    RESEARCHING = "RESEARCHING"
    SHORTLISTED = "SHORTLISTED"
    APPLIED = "APPLIED"
    SCHOLARSHIP_APPLIED = "SCHOLARSHIP_APPLIED"
    ADMISSION_RECEIVED = "ADMISSION_RECEIVED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


ALL_ENUMS: dict[str, type[StrEnum]] = {
    "funding_class": FundingClass,
    "opportunity_type": OpportunityType,
    "source_tier": SourceTier,
    "match_class": MatchClass,
    "scholarship_match": ScholarshipMatch,
    "deadline_status": DeadlineStatus,
    "job_status": JobStatus,
    "tracker_status": TrackerStatus,
}
