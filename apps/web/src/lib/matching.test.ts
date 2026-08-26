import { describe, expect, it } from "vitest";
import {
  classifyStrategy,
  computeScore,
  deadlineDimension,
  fundingDimension,
  languageDimension,
  relevanceDimension,
  tuitionDimension,
  DEFAULT_WEIGHTS,
} from "@/lib/matching";
import type { ProgramRow } from "@/lib/types";

function row(overrides: Partial<ProgramRow>): ProgramRow {
  return {
    id: "x", country: "Italy", city: "Milan", university: "Politecnico di Milano",
    program: "MSc CS", degree: "MSc", fieldTags: ["cs"], language: "English",
    durationMonths: 24, tuitionEurPerYear: 0, fundingClass: "TUITION_FREE",
    scholarshipName: null, ieltsOverall: 6.5, moiAccepted: "NOT_SPECIFIED",
    intake: "Fall 2027", deadline: "2027-03-15", deadlineStatus: "OPEN",
    daysRemaining: 200, partTimeWork: "NOT_SPECIFIED", matchClass: null,
    score: null, isJointProgram: false, ...overrides,
  };
}

describe("fundingDimension", () => {
  it("ranks stipend above tuition-free above self-funded", () => {
    expect(fundingDimension("FULLY_FUNDED_STIPEND")).toBeGreaterThan(fundingDimension("TUITION_FREE"));
    expect(fundingDimension("TUITION_FREE")).toBeGreaterThan(fundingDimension("SELF_FUNDED"));
  });

  it("not-specified gets neutral-low, not zero", () => {
    expect(fundingDimension("NOT_SPECIFIED")).toBe(0.3);
  });
});

describe("tuitionDimension", () => {
  it("free is best, null is neutral-low", () => {
    expect(tuitionDimension(0)).toBe(1.0);
    expect(tuitionDimension(null)).toBe(0.3);
  });

  it("monotonically decreases with cost", () => {
    expect(tuitionDimension(500)).toBeGreaterThan(tuitionDimension(2500));
    expect(tuitionDimension(2500)).toBeGreaterThan(tuitionDimension(5000));
    expect(tuitionDimension(5000)).toBeGreaterThan(tuitionDimension(20000));
  });
});

describe("languageDimension", () => {
  it("MOI accepted beats high IELTS", () => {
    expect(languageDimension(null, true)).toBeGreaterThan(languageDimension(7.5, "NOT_SPECIFIED"));
  });

  it("lower IELTS requirement scores higher", () => {
    expect(languageDimension(6.0, "NOT_SPECIFIED")).toBeGreaterThan(languageDimension(7.0, "NOT_SPECIFIED"));
  });
});

describe("deadlineDimension", () => {
  it("closed scores zero but stays visible", () => {
    expect(deadlineDimension("CLOSED", null)).toBe(0);
  });

  it("approaching is most actionable", () => {
    expect(deadlineDimension("APPROACHING", 10)).toBe(1.0);
    expect(deadlineDimension("APPROACHING", 10)).toBeGreaterThan(deadlineDimension("OPEN", 200));
  });

  it("unknown is low but not zero", () => {
    expect(deadlineDimension("UNKNOWN", null)).toBeGreaterThan(0);
  });
});

describe("relevanceDimension", () => {
  it("more CSE tags score higher, capped", () => {
    expect(relevanceDimension(["cs"])).toBeLessThan(relevanceDimension(["cs", "ai"]));
    expect(relevanceDimension(["cs", "ai", "ml", "systems"])).toBeLessThanOrEqual(1);
  });

  it("no tags is low but not zero", () => {
    expect(relevanceDimension([])).toBe(0.3);
  });
});

describe("computeScore", () => {
  it("strong funded program outscores expensive self-funded", () => {
    const good = computeScore(row({
      fundingClass: "FULLY_FUNDED_STIPEND", tuitionEurPerYear: 0,
      deadlineStatus: "APPROACHING", daysRemaining: 20,
    }));
    const bad = computeScore(row({
      fundingClass: "SELF_FUNDED", tuitionEurPerYear: 15000,
      deadlineStatus: "CLOSED", daysRemaining: null,
    }));
    expect(good.score).toBeGreaterThan(bad.score);
  });

  it("score is 0-100 integer", () => {
    const { score } = computeScore(row({}));
    expect(Number.isInteger(score)).toBe(true);
    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(100);
  });

  it("weights shift outcomes: funding-heavy vs tuition-heavy", () => {
    const freeButCostly = row({ fundingClass: "TUITION_FREE", tuitionEurPerYear: 12000 });
    const fundedWeights = { ...DEFAULT_WEIGHTS, funding: 0.8, tuition: 0.05, language: 0.05, deadline: 0.05, relevance: 0.05 };
    const tuitionWeights = { ...DEFAULT_WEIGHTS, funding: 0.05, tuition: 0.8, language: 0.05, deadline: 0.05, relevance: 0.05 };
    expect(computeScore(freeButCostly, fundedWeights).score)
      .toBeGreaterThan(computeScore(freeButCostly, tuitionWeights).score);
  });

  it("zero weights yields zero without crash", () => {
    const zero = { funding: 0, tuition: 0, language: 0, deadline: 0, relevance: 0 };
    expect(computeScore(row({}), zero).score).toBe(0);
  });
});

describe("classifyStrategy", () => {
  it("high score + competitive funding = REACH", () => {
    expect(classifyStrategy(85, "FULLY_FUNDED_STIPEND")).toBe("REACH");
  });

  it("high score without competitive funding = TARGET", () => {
    expect(classifyStrategy(85, "LOW_TUITION")).toBe("TARGET");
  });

  it("low score = SAFETY", () => {
    expect(classifyStrategy(20, "TUITION_FREE")).toBe("SAFETY");
  });
});
