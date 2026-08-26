"use client";
/* Scholarly Ledger style: provenance-led tables with tier stamps, visible dates, and quotable source excerpts. */
import { ExternalLink } from 'lucide-react';
import type { EvidenceEntry } from '@/lib/types';

const tierLabel = { TIER1_OFFICIAL: 'Tier 1 · official', TIER2_PORTAL: 'Tier 2 · portal', TIER3_COMMUNITY: 'Tier 3 · community' } as const;

export function EvidenceTable({ entries }: { entries: EvidenceEntry[] }) {
  return <div className="overflow-hidden rounded-xl border border-border bg-card">
    <div className="border-b border-border bg-secondary/40 px-4 py-3"><p className="data-label">Evidence register</p><p className="mt-1 text-xs text-muted-foreground">Sample data for prototype · always verify at source before acting.</p></div>
    <div className="divide-y divide-border">{entries.map((entry) => <div key={`${entry.field}-${entry.sourceUrl}`} className="grid gap-3 px-4 py-4 md:grid-cols-[150px_1fr_150px]">
      <div><p className="text-sm font-bold">{entry.field}</p><p className="mt-1 text-xs text-muted-foreground">{entry.value}</p></div>
      <blockquote className="border-l-2 border-primary/40 pl-3 text-sm leading-6 text-muted-foreground">“{entry.quote}”</blockquote>
      <div className="flex flex-row gap-2 md:flex-col md:items-start"><span className="rounded border border-border px-1.5 py-1 text-[10px] font-bold uppercase tracking-wide text-muted-foreground">{tierLabel[entry.sourceTier]}</span><a href={entry.sourceUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-bold text-primary hover:underline">Source <ExternalLink className="h-3 w-3" /></a><span className="text-[11px] text-muted-foreground">Retrieved {entry.retrievedAt}</span></div>
    </div>)}</div>
  </div>;
}
