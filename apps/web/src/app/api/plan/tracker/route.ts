import { createClient } from "@/lib/supabase/server";
import { NextResponse, type NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const VALID_STATUSES = new Set([
  "INTERESTED", "RESEARCHING", "SHORTLISTED", "APPLIED",
  "SCHOLARSHIP_APPLIED", "ADMISSION_RECEIVED", "ACCEPTED", "REJECTED",
]);

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "sign in required" }, { status: 401 });
  }
  const body = await request.json().catch(() => null);
  const programId = body?.programId;
  const status = body?.status;
  if (typeof programId !== "string" || !programId) {
    return NextResponse.json({ error: "invalid programId" }, { status: 400 });
  }
  if (typeof status !== "string" || !VALID_STATUSES.has(status)) {
    return NextResponse.json({ error: "invalid status" }, { status: 400 });
  }
  const { error } = await supabase
    .from("tracker_entries")
    .upsert(
      { user_id: user.id, program_id: programId, status, updated_at: new Date().toISOString() },
      { onConflict: "user_id,program_id" },
    );
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }
  return NextResponse.json({ ok: true });
}

export async function DELETE(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "sign in required" }, { status: 401 });
  }
  const { searchParams } = new URL(request.url);
  const programId = searchParams.get("programId");
  if (!programId) {
    return NextResponse.json({ error: "invalid programId" }, { status: 400 });
  }
  const { error } = await supabase
    .from("tracker_entries")
    .delete()
    .eq("user_id", user.id)
    .eq("program_id", programId);
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }
  return NextResponse.json({ ok: true });
}
