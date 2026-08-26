import { createClient } from "@/lib/supabase/server";
import type { ProgramRowDb } from "@/lib/db-types";
import type { EvidenceEntry, ProgramRow } from "@/lib/types";

interface JoinedRow extends ProgramRowDb {
  universities: {
    name: string;
    website: string | null;
    countries: { name: string } | null;
  } | null;
}

function daysRemaining(deadlineIso: string | null): number | null {
  if (!deadlineIso) return null;
  const deadline = new Date(deadlineIso);
  if (Number.isNaN(deadline.getTime())) return null;
  const diff = deadline.getTime() - Date.now();
  return Math.ceil(diff / 86_400_000);
}

export function mapDbProgram(row: JoinedRow): ProgramRow {
  const uni = row.universities;
  return {
    id: row.id,
    country: uni?.countries?.name ?? "—",
    city: "",
    university: uni?.name ?? "—",
    program: row.name,
    degree: row.degree ?? "Master's",
    fieldTags: row.field_tags ?? [],
    language: row.language ?? "—",
    durationMonths: row.duration_months ?? 0,
    tuitionEurPerYear:
      row.tuition_eur_per_year === null ? null : Number(row.tuition_eur_per_year),
    fundingClass: row.funding_class,
    scholarshipName: null,
    ieltsOverall: row.ielts && typeof row.ielts === "object" && "overall" in row.ielts
      ? (row.ielts.overall ?? null)
      : null,
    moiAccepted:
      row.moi_policy === "ACCEPTED"
        ? true
        : row.moi_policy === "NOT_ACCEPTED"
          ? false
          : "NOT_SPECIFIED",
    intake: Array.isArray(row.intakes) && row.intakes[0]?.name ? row.intakes[0].name : "—",
    deadline: row.program_deadline,
    deadlineStatus: row.deadline_status,
    daysRemaining: daysRemaining(row.program_deadline),
    partTimeWork: "NOT_SPECIFIED",
    matchClass: null,
    score: null,
    isJointProgram: row.is_joint_program,
  };
}

export function mapDbEvidence(entries: unknown): EvidenceEntry[] {
  if (!Array.isArray(entries)) return [];
  return entries.flatMap((raw) => {
    if (typeof raw !== "object" || raw === null) return [];
    const e = raw as Record<string, unknown>;
    if (typeof e.source_url !== "string") return [];
    return [{
      field: String(e.field ?? ""),
      value: String(e.value ?? ""),
      sourceUrl: e.source_url,
      sourceTier: "TIER1_OFFICIAL",
      quote: String(e.quote ?? ""),
      retrievedAt: String(e.retrieved_at ?? ""),
    } satisfies EvidenceEntry];
  });
}

export async function fetchProgramRows(limit = 500): Promise<{
  rows: ProgramRow[];
  evidenceCounts: Record<string, number>;
}> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("programs")
    .select("*, universities(name, website, countries(name))")
    .order("last_verified_at", { ascending: false, nullsFirst: false })
    .limit(limit);
  if (error) throw new Error(error.message);
  const joined = (data as unknown as JoinedRow[]) ?? [];
  const evidenceCounts: Record<string, number> = {};
  for (const row of joined) {
    evidenceCounts[row.id] = Array.isArray(row.evidence) ? row.evidence.length : 0;
  }
  return { rows: joined.map(mapDbProgram), evidenceCounts };
}

export async function fetchProgramById(
  id: string,
): Promise<{
  program: ProgramRow;
  evidence: EvidenceEntry[];
  changes: Array<{ field: string; oldValue: unknown; newValue: unknown; changedAt: string }>;
} | null> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("programs")
    .select("*, universities(name, website, countries(name))")
    .eq("id", id)
    .maybeSingle();
  if (error) throw new Error(error.message);
  const row = data as unknown as JoinedRow | null;
  if (!row) return null;
  const { data: changes } = await supabase
    .from("change_log")
    .select("field, old_value, new_value, changed_at")
    .eq("entity_id", id)
    .order("changed_at", { ascending: false })
    .limit(20);
  return {
    program: mapDbProgram(row),
    evidence: mapDbEvidence(row.evidence),
    changes: (changes ?? []).map((c) => ({
      field: String(c.field ?? ""),
      oldValue: c.old_value,
      newValue: c.new_value,
      changedAt: String(c.changed_at ?? ""),
    })),
  };
}

export interface CountryPageData {
  country: {
    id: string;
    name: string;
    pack: Record<string, unknown>;
    researched: boolean;
  } | null;
  programs: ProgramRow[];
}

export async function fetchCountryPage(code: string): Promise<CountryPageData> {
  const supabase = await createClient();
  const { data: country } = await supabase
    .from("countries")
    .select("id, name, pack")
    .eq("id", code.toUpperCase())
    .maybeSingle();
  const { data: programRows } = await supabase
    .from("programs")
    .select("*, universities!inner(name, website, countries(name))")
    .eq("universities.country_id", code.toUpperCase())
    .order("last_verified_at", { ascending: false, nullsFirst: false })
    .limit(200);
  const pack = (country?.pack ?? {}) as Record<string, unknown>;
  return {
    country: country
      ? {
          id: country.id,
          name: country.name,
          pack,
          researched: Object.keys(pack).length > 0,
        }
      : null,
    programs: ((programRows ?? []) as unknown as JoinedRow[]).map(mapDbProgram),
  };
}
