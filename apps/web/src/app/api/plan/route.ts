import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

interface ProgramSummary {
  id: string;
  name: string;
  university: string;
  country: string;
  fundingClass: string;
  deadline: string | null;
  deadlineStatus: string;
}

async function programSummaries(ids: string[]): Promise<Record<string, ProgramSummary>> {
  if (ids.length === 0) return {};
  const supabase = await createClient();
  const { data } = await supabase
    .from("programs")
    .select("id, name, funding_class, program_deadline, deadline_status, universities(name, countries(name))")
    .in("id", ids);
  const map: Record<string, ProgramSummary> = {};
  for (const row of data ?? []) {
    const typed = row as unknown as {
      id: string; name: string; funding_class: string; program_deadline: string | null;
      deadline_status: string;
      universities: { name: string; countries: { name: string } | null } | null;
    };
    map[typed.id] = {
      id: typed.id,
      name: typed.name,
      university: typed.universities?.name ?? "—",
      country: typed.universities?.countries?.name ?? "—",
      fundingClass: typed.funding_class,
      deadline: typed.program_deadline,
      deadlineStatus: typed.deadline_status,
    };
  }
  return map;
}

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "sign in required" }, { status: 401 });
  }

  const [saved, tracker] = await Promise.all([
    supabase
      .from("saved_items")
      .select("entity_type, entity_id, note, created_at")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false }),
    supabase
      .from("tracker_entries")
      .select("program_id, status, updated_at, programs(name, funding_class, program_deadline, deadline_status, universities(name, countries(name)))")
      .eq("user_id", user.id)
      .order("updated_at", { ascending: false }),
  ]);

  const savedProgramIds = (saved.data ?? [])
    .filter((item) => item.entity_type === "PROGRAM")
    .map((item) => item.entity_id as string);
  const summaries = await programSummaries(savedProgramIds);

  const trackerRows = (tracker.data ?? []) as unknown as Array<{
    program_id: string; status: string; updated_at: string;
    programs: {
      name: string; funding_class: string; program_deadline: string | null; deadline_status: string;
      universities: { name: string; countries: { name: string } | null } | null;
    } | null;
  }>;

  return NextResponse.json({
    saved: (saved.data ?? []).map((item) => ({
      entityType: item.entity_type,
      entityId: item.entity_id,
      note: item.note,
      createdAt: item.created_at,
      program: item.entity_type === "PROGRAM" ? summaries[item.entity_id as string] ?? null : null,
    })),
    tracker: trackerRows.map((entry) => ({
      programId: entry.program_id,
      status: entry.status,
      updatedAt: entry.updated_at,
      program: entry.programs
        ? {
            id: entry.program_id,
            name: entry.programs.name,
            university: entry.programs.universities?.name ?? "—",
            country: entry.programs.universities?.countries?.name ?? "—",
            fundingClass: entry.programs.funding_class,
            deadline: entry.programs.program_deadline,
            deadlineStatus: entry.programs.deadline_status,
          }
        : null,
    })),
  });
}
