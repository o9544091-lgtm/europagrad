"use client";

import { useEffect, useState } from "react";
import { LoaderCircle, Radar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

interface JobRow {
  id: string;
  status: string;
  progress: Record<string, unknown>;
  countries: string[];
  depth_level: string;
  error: string | null;
}

const ISO_RE = /^[A-Za-z]{2}$/;

export function ResearchTrigger() {
  const [codes, setCodes] = useState("IT");
  const [depth, setDepth] = useState("L1");
  const [submitting, setSubmitting] = useState(false);
  const [jobs, setJobs] = useState<JobRow[]>([]);

  async function refreshJobs() {
    const resp = await fetch("/api/research/status", { cache: "no-store" });
    if (resp.ok) {
      const body = await resp.json();
      setJobs(body.jobs ?? []);
    }
  }

  useEffect(() => {
    void refreshJobs();
  }, []);

  useEffect(() => {
    const hasActive = jobs.some((j) => j.status === "PENDING" || j.status === "RUNNING");
    if (!hasActive) return;
    const timer = window.setInterval(() => void refreshJobs(), 5000);
    return () => window.clearInterval(timer);
  }, [jobs]);

  async function trigger() {
    const parsed = codes.split(",").map((c) => c.trim().toUpperCase()).filter((c) => ISO_RE.test(c));
    if (parsed.length === 0) {
      toast.error("Enter valid 2-letter country codes, e.g. IT,DE");
      return;
    }
    setSubmitting(true);
    const resp = await fetch("/api/research/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ countries: parsed, depth }),
    });
    setSubmitting(false);
    const body = await resp.json().catch(() => ({}));
    if (resp.ok) {
      toast.success(`Research queued for ${parsed.join(", ")} (${depth}). Progress appears below.`);
      await refreshJobs();
    } else {
      toast.error(body.error ?? "Could not start the research run.");
    }
  }

  return (
    <div className="ledger-card p-5">
      <div className="flex items-center gap-2"><Radar className="h-5 w-5 text-primary" /><p className="font-extrabold">Run a research pass</p></div>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">
        Queues a live agent run (registry inventory → sitemap harvest → citation-checked extraction).
        New programmes appear here when it finishes.
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Input
          value={codes}
          onChange={(e) => setCodes(e.target.value)}
          placeholder="Country codes: IT,DE"
          aria-label="Country codes"
          className="w-44"
        />
        <select
          value={depth}
          onChange={(e) => setDepth(e.target.value)}
          aria-label="Depth level"
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
        >
          <option value="L1">L1 Quick</option>
          <option value="L2">L2 Standard</option>
          <option value="L3">L3 Exhaustive</option>
        </select>
        <Button onClick={() => void trigger()} disabled={submitting} className="gap-2">
          {submitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Radar className="h-4 w-4" />}
          {submitting ? "Queuing…" : "Start research"}
        </Button>
      </div>
      {jobs.length > 0 && (
        <div className="mt-4 space-y-2">
          {jobs.map((job) => {
            const progress = job.progress as { phase?: string; done?: number; total?: number };
            return (
              <div key={job.id} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-secondary/30 px-3 py-2 text-xs">
                <span className="font-bold">{job.countries.join(", ")} · {job.depth_level}</span>
                <span className="text-muted-foreground">
                  {job.status === "RUNNING" && progress.phase
                    ? `${progress.phase} ${progress.done ?? 0}/${progress.total ?? "?"}`
                    : job.status}
                </span>
                <span className={job.status === "DONE" ? "font-bold text-emerald-500" : job.status === "FAILED" ? "font-bold text-destructive" : "text-muted-foreground"}>
                  {job.status}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
