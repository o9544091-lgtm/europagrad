"use client";
/* EuropaGrad report: generated from the researched dataset with print-friendly layout. */
import { useMemo } from 'react';
import Link from 'next/link';
import { Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DeadlineBadge, FundingBadge } from '@/components/status-badge';
import type { ProgramRow } from '@/lib/types';

function group(rows: ProgramRow[], predicate: (p: ProgramRow) => boolean) {
  return rows.filter(predicate).slice(0, 8);
}

export default function ReportPage({ rows }: { rows: ProgramRow[] }) {
  const groups = useMemo(() => ({
    funded: group(rows, (p) => ['FULLY_FUNDED', 'FULLY_FUNDED_STIPEND'].includes(p.fundingClass)),
    tuitionFree: group(rows, (p) => ['TUITION_FREE', 'TUITION_WAIVER'].includes(p.fundingClass)),
    noIelts: group(rows, (p) => p.ieltsOverall === null),
    moi: group(rows, (p) => p.moiAccepted === true),
    deadlines: [...rows]
      .filter((p) => p.deadline && p.deadlineStatus !== 'CLOSED')
      .sort((a, b) => (a.daysRemaining ?? 9999) - (b.daysRemaining ?? 9999))
      .slice(0, 10),
  }), [rows]);

  const strategy = useMemo(() => ({
    reach: rows.filter((p) => (p.score ?? 0) >= 70).slice(0, 6),
    target: rows.filter((p) => (p.score ?? 0) >= 45 && (p.score ?? 0) < 70).slice(0, 6),
    safety: rows.filter((p) => (p.score ?? 0) < 45).slice(0, 6),
  }), [rows]);

  return <div className="container soft-enter py-8 pb-20 print:py-4">
    <div className="flex items-center justify-between print:hidden">
      <p className="data-label">Research output</p>
      <Button variant="outline" size="sm" className="gap-2" onClick={() => window.print()}><Printer className="h-4 w-4" />Print / save PDF</Button>
    </div>
    <h1 className="mt-4 text-3xl font-extrabold tracking-tight sm:text-4xl">Research report</h1>
    <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
      Generated from {rows.length} researched programme records. Every claim traces to evidence entries
      on each programme page — re-verify deadlines and eligibility at their official sources before applying.
    </p>

    <section className="mt-8 grid gap-5 sm:grid-cols-3">
      {([['Best funded', groups.funded], ['Tuition-free routes', groups.tuitionFree], ['Without stated IELTS', groups.noIelts]] as const).map(([title, items]) => (
        <div key={title} className="ledger-card p-5">
          <p className="data-label">{title}</p>
          {items.length === 0 ? <p className="mt-3 text-sm text-muted-foreground">None in the current dataset.</p> : (
            <ul className="mt-3 space-y-2">
              {items.map((p) => <li key={p.id}><Link href={`/programs/${p.id}`} className="text-sm font-bold hover:text-primary">{p.program}</Link><p className="text-xs text-muted-foreground">{p.university} · {p.country}</p></li>)}
            </ul>
          )}
        </div>
      ))}
    </section>

    <section className="mt-8">
      <p className="data-label">Upcoming deadlines (open or unpublished)</p>
      <div className="mt-3 overflow-x-auto rounded-xl border border-border bg-card">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="bg-secondary/40 text-[11px] font-bold uppercase tracking-[0.11em] text-muted-foreground"><tr><th className="px-4 py-3">Programme</th><th className="px-4 py-3">Deadline</th><th className="px-4 py-3">Status</th></tr></thead>
          <tbody>{groups.deadlines.length === 0 ? <tr><td className="px-4 py-4 text-muted-foreground" colSpan={3}>No open deadlines in the dataset.</td></tr> : groups.deadlines.map((p) => <tr key={p.id} className="ledger-row"><td className="px-4 py-3"><p className="font-bold">{p.program}</p><p className="text-xs text-muted-foreground">{p.university}</p></td><td className="px-4 py-3 tabular">{p.deadline ?? '—'}</td><td className="px-4 py-3"><DeadlineBadge status={p.deadlineStatus} days={p.daysRemaining} /></td></tr>)}</tbody>
        </table>
      </div>
    </section>

    <section className="mt-8 grid gap-5 lg:grid-cols-3">
      {([['Reach', strategy.reach], ['Target', strategy.target], ['Safety / lower-risk', strategy.safety]] as const).map(([title, items]) => (
        <div key={title} className="ledger-card p-5">
          <p className="data-label">{title}</p>
          {items.length === 0 ? <p className="mt-3 text-sm text-muted-foreground">No programmes in this band yet.</p> : (
            <ul className="mt-3 space-y-2">
              {items.map((p) => <li key={p.id} className="text-sm"><Link href={`/programs/${p.id}`} className="font-bold hover:text-primary">{p.program}</Link><span className="ml-2 text-xs text-muted-foreground">{p.university}</span><div className="mt-1"><FundingBadge funding={p.fundingClass} /></div></li>)}
            </ul>
          )}
        </div>
      ))}
    </section>

    <p className="mt-10 border-t border-border pt-4 text-xs leading-5 text-muted-foreground">
      Strategy bands are evidence-based groupings, never admission guarantees. MOI acceptance varies by
      intake and department. Generated {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}.
    </p>
  </div>;
}
