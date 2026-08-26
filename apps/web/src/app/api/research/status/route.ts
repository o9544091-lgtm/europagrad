import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "sign in required" }, { status: 401 });
  }
  const { data } = await supabase
    .from("research_jobs")
    .select("id, status, progress, countries, depth_level, error, created_at, finished_at")
    .eq("triggered_by", user.id)
    .order("created_at", { ascending: false })
    .limit(5);
  return NextResponse.json({ jobs: data ?? [] });
}
