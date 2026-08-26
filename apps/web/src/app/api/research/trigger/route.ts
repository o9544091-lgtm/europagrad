import { createClient } from "@/lib/supabase/server";
import { NextResponse, type NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const VALID_DEPTHS = new Set(["L1", "L2", "L3"]);
const ISO2_RE = /^[A-Z]{2}$/;

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "sign in required" }, { status: 401 });
  }

  const githubToken = process.env.GITHUB_TOKEN;
  const githubRepo = process.env.GITHUB_REPO;
  if (!githubToken || !githubRepo) {
    return NextResponse.json(
      { error: "Research runner not configured (missing GITHUB_TOKEN/GITHUB_REPO)." },
      { status: 503 },
    );
  }

  const body = await request.json().catch(() => null);
  const rawCountries = Array.isArray(body?.countries) ? body.countries : [];
  const countries = rawCountries
    .filter((c: unknown): c is string => typeof c === "string" && ISO2_RE.test(c))
    .slice(0, 8);
  const depth = typeof body?.depth === "string" && VALID_DEPTHS.has(body.depth) ? body.depth : "L1";

  if (countries.length === 0) {
    return NextResponse.json({ error: "provide 1-8 valid ISO country codes" }, { status: 400 });
  }

  const active = await supabase
    .from("research_jobs")
    .select("id")
    .eq("status", "RUNNING")
    .eq("triggered_by", user.id);
  if ((active.data?.length ?? 0) >= 2) {
    return NextResponse.json(
      { error: "You already have 2 research runs in progress. Wait for them to finish." },
      { status: 429 },
    );
  }

  const { data: job, error: jobError } = await supabase
    .from("research_jobs")
    .insert({
      triggered_by: user.id,
      countries,
      depth_level: depth,
      status: "PENDING",
      progress: { phase: "queued" },
    })
    .select("id")
    .single();
  if (jobError || !job) {
    return NextResponse.json({ error: "could not queue job" }, { status: 500 });
  }

  const dispatch = await fetch(
    `https://api.github.com/repos/${githubRepo}/actions/workflows/agent-research.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${githubToken}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ref: "main",
        inputs: {
          countries: countries.join(","),
          depth,
          dry_run: "false",
          extractor: "auto",
          limit: "25",
          job_id: job.id,
        },
      }),
    },
  );
  if (!dispatch.ok) {
    await supabase.from("research_jobs").update({ status: "FAILED", error: `dispatch failed: ${dispatch.status}` }).eq("id", job.id);
    return NextResponse.json({ error: `GitHub dispatch failed (${dispatch.status})` }, { status: 502 });
  }

  return NextResponse.json({ jobId: job.id, countries, depth });
}
