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
  matchClass: MatchClass; score: number;
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
