import type { FundingClass, DeadlineStatus, ProgramRow } from "@/lib/types";

export interface RankWeights {
  funding: number;
  tuition: number;
  language: number;
  deadline: number;
  relevance: number;
}

export const DEFAULT_WEIGHTS: RankWeights = {
  funding: 0.35,
  tuition: 0.25,
  language: 0.15,
  deadline: 0.15,
  relevance: 0.10,
};

export const WEIGHT_LABELS: Record<keyof RankWeights, string> = {
  funding: "Funding",
  tuition: "Tuition",
  language: "Language",
  deadline: "Deadline",
  relevance: "Relevance",
};

const FUNDING_SCORE: Record<FundingClass, number> = {
  FULLY_FUNDED_STIPEND: 1.0,
  FULLY_FUNDED: 0.95,
  TUITION_FREE: 0.85,
  TUITION_WAIVER: 0.7,
  RESEARCH_FUNDED: 0.65,
  ASSISTANTSHIP: 0.6,
  PARTIAL_SCHOLARSHIP: 0.5,
  LOW_TUITION: 0.4,
  NOT_SPECIFIED: 0.3,
  SELF_FUNDED: 0.1,
};

export function fundingDimension(fundingClass: FundingClass): number {
  return FUNDING_SCORE[fundingClass] ?? 0.3;
}

export function tuitionDimension(tuitionEurPerYear: number | null): number {
  if (tuitionEurPerYear === null) return 0.3;
  if (tuitionEurPerYear <= 0) return 1.0;
  if (tuitionEurPerYear <= 1000) return 0.85;
  if (tuitionEurPerYear <= 3000) return 0.7;
  if (tuitionEurPerYear <= 6000) return 0.5;
  if (tuitionEurPerYear <= 10000) return 0.3;
  return 0.15;
}

export function languageDimension(
  ieltsOverall: number | null,
  moiAccepted: boolean | "NOT_SPECIFIED",
): number {
  if (moiAccepted === true) return 0.9;
  if (ieltsOverall === null) return 0.5;
  if (ieltsOverall <= 6.0) return 0.85;
  if (ieltsOverall <= 6.5) return 0.7;
  if (ieltsOverall <= 7.0) return 0.5;
  return 0.35;
}

export function deadlineDimension(
  deadlineStatus: DeadlineStatus,
  daysRemaining: number | null,
): number {
  switch (deadlineStatus) {
    case "APPROACHING":
      return 1.0;
    case "OPEN":
      if (daysRemaining === null) return 0.7;
      if (daysRemaining > 90) return 0.9;
      if (daysRemaining >= 30) return 1.0;
      return 0.8;
    case "NOT_YET_OPEN":
      return 0.6;
    case "FUTURE_NOT_PUBLISHED":
      return 0.5;
    case "UNKNOWN":
      return 0.4;
    case "CLOSED":
      return 0;
    default:
      return 0.4;
  }
}

const CSE_TAGS = new Set([
  "cs", "ai", "ml", "data-science", "software-engineering", "cybersecurity",
  "information-systems", "it", "robotics", "computer-engineering", "embedded",
  "hci", "systems",
]);

export function relevanceDimension(fieldTags: string[]): number {
  const hits = fieldTags.filter((t) => CSE_TAGS.has(t.toLowerCase())).length;
  if (hits === 0) return 0.3;
  return Math.min(1, 0.4 + hits * 0.3);
}

export interface ScoreBreakdown {
  score: number;
  dimensions: Record<keyof RankWeights, number>;
}

export function computeScore(
  program: Pick<
    ProgramRow,
    "fundingClass" | "tuitionEurPerYear" | "ieltsOverall" | "moiAccepted" | "deadlineStatus" | "daysRemaining" | "fieldTags"
  >,
  weights: RankWeights = DEFAULT_WEIGHTS,
): ScoreBreakdown {
  const dimensions = {
    funding: fundingDimension(program.fundingClass),
    tuition: tuitionDimension(program.tuitionEurPerYear),
    language: languageDimension(program.ieltsOverall, program.moiAccepted),
    deadline: deadlineDimension(program.deadlineStatus, program.daysRemaining),
    relevance: relevanceDimension(program.fieldTags),
  };
  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  if (totalWeight <= 0) return { score: 0, dimensions };
  const weighted = (Object.keys(dimensions) as Array<keyof RankWeights>)
    .reduce((sum, key) => sum + weights[key] * dimensions[key], 0);
  return { score: Math.round((weighted / totalWeight) * 100), dimensions };
}

export type StrategyClass = "REACH" | "TARGET" | "SAFETY";

export function classifyStrategy(score: number, fundingClass: FundingClass): StrategyClass {
  const competitiveFunding =
    fundingClass === "FULLY_FUNDED_STIPEND" || fundingClass === "FULLY_FUNDED";
  if (score >= 70 && competitiveFunding) return "REACH";
  if (score >= 45) return competitiveFunding ? "REACH" : "TARGET";
  return "SAFETY";
}

export function enrichWithScores<T extends ProgramRow>(
  rows: T[],
  weights: RankWeights = DEFAULT_WEIGHTS,
): T[] {
  return rows.map((row) => ({
    ...row,
    score: computeScore(row, weights).score,
  }));
}
