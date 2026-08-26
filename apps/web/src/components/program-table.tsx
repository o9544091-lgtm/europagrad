"use client";
/* Scholarly Ledger style: dense desktop ledger that collapses into clear, touch-friendly research cards below 768px. */
import { useRouter } from 'next/navigation';
import { ArrowUpRight, Info, Sparkles } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { ProgramRow } from '@/lib/types';
import { DeadlineBadge, deadlineStripClass, FundingBadge, MatchPill } from './status-badge';

function money(value: number | null) { return value === null ? '—' : value === 0 ? '€0' : `€${value.toLocaleString('en-US')}`; }

export function ProgramTable({ rows, compact = false }: { rows: ProgramRow[]; compact?: boolean }) {
  const router = useRouter();
  const navigate = (id: string) => router.push(`/programs/${id}`);
  return <>
    <div className="hidden overflow-x-auto rounded-xl border border-border bg-card md:block">
      <table className="w-full min-w-[1050px] text-left text-sm">
        <thead className="border-b border-border bg-secondary/40"><tr className="text-[11px] font-bold uppercase tracking-[0.11em] text-muted-foreground">
          <th className="px-4 py-3">Rank</th><th className="px-4 py-3">Institution / programme</th>{!compact && <th className="px-4 py-3">Funding</th>}<th className="px-4 py-3">Tuition / yr</th>{!compact && <th className="px-4 py-3">Language</th>}<th className="px-4 py-3">Deadline</th><th className="px-4 py-3">Match</th><th className="px-4 py-3 text-right">Score</th>
        </tr></thead>
        <tbody>{rows.map((program) => <tr key={program.id} onClick={() => navigate(program.id)} className={`ledger-row border-l-4 ${deadlineStripClass[program.deadlineStatus]} cursor-pointer transition-colors hover:bg-primary/[0.035] focus-within:bg-primary/[0.035]`}>
          <td className="px-4 py-4 tabular font-bold text-muted-foreground">{program.rank ?? '—'}</td>
          <td className="px-4 py-4"><div className="flex items-start gap-2"><div><p className="font-bold text-foreground">{program.university}</p><p className="mt-0.5 text-xs text-muted-foreground">{program.program} {program.isJointProgram && <span className="ml-1 inline-flex rounded bg-violet-100 px-1.5 py-0.5 font-bold text-violet-800 dark:bg-violet-950 dark:text-violet-200">JOINT</span>}</p><p className="mt-1 text-[11px] text-muted-foreground">{program.city}, {program.country}</p></div></div></td>
          {!compact && <td className="px-4 py-4"><FundingBadge funding={program.fundingClass} /><p className="mt-1.5 max-w-32 truncate text-[11px] text-muted-foreground">{program.scholarshipName ?? 'No linked award'}</p></td>}
          <td className="px-4 py-4 tabular font-semibold">{money(program.tuitionEurPerYear)}{program.tuitionEurPerYear !== null && <span className="block text-[11px] font-normal text-muted-foreground">per year</span>}</td>
          {!compact && <td className="px-4 py-4"><span className="font-medium">IELTS {program.ieltsOverall ?? '—'}</span><span className="block text-[11px] text-muted-foreground">MOI {program.moiAccepted === true ? 'may be accepted' : program.moiAccepted === false ? 'not shown' : 'verify'}</span></td>}
          <td className="px-4 py-4"><DeadlineBadge status={program.deadlineStatus} days={program.daysRemaining} /><p className="mt-1 text-[11px] text-muted-foreground">{program.deadline ?? 'Date pending'}</p></td>
          <td className="px-4 py-4"><MatchPill match={program.matchClass} /></td>
          <td className="px-4 py-4 text-right"><Tooltip><TooltipTrigger asChild><span className="inline-flex items-center gap-1 tabular text-lg font-extrabold text-primary">{program.score}<Info className="h-3.5 w-3.5 text-muted-foreground" /></span></TooltipTrigger><TooltipContent><p>Sample score: funding 35 · fit 30 · tuition 20 · deadline 15</p></TooltipContent></Tooltip></td>
        </tr>)}</tbody>
      </table>
    </div>
    <div className="space-y-3 md:hidden">{rows.map((program) => <button type="button" key={program.id} onClick={() => navigate(program.id)} className={`ledger-card w-full border-l-4 ${deadlineStripClass[program.deadlineStatus]} p-4 text-left transition-transform active:scale-[0.99]`}>
      <div className="flex items-start justify-between gap-3"><div><p className="data-label">#{program.rank ?? '—'} · {program.country}</p><h3 className="mt-1 font-bold">{program.university}</h3><p className="mt-1 text-sm text-muted-foreground">{program.program}</p></div><span className="tabular text-xl font-extrabold text-primary">{program.score}</span></div>
      <div className="mt-4 flex flex-wrap gap-2"><FundingBadge funding={program.fundingClass} /><DeadlineBadge status={program.deadlineStatus} days={program.daysRemaining} /><MatchPill match={program.matchClass} /></div>
      <div className="mt-4 flex items-center justify-between border-t border-border pt-3 text-xs text-muted-foreground"><span className="tabular">{money(program.tuitionEurPerYear)} / yr</span><span className="inline-flex items-center gap-1 font-bold text-primary">Inspect evidence <ArrowUpRight className="h-3.5 w-3.5" /></span></div>
    </button>)}</div>
  </>;
}

export function EmptyResults({ onReset }: { onReset: () => void }) {
  return <div className="ledger-card surface-dots flex min-h-72 flex-col items-center justify-center p-8 text-center"><Sparkles className="h-7 w-7 text-primary" /><h3 className="mt-4 text-lg font-extrabold">No sample records fit these filters</h3><p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">Broaden a funding or country condition to return to the representative programme set.</p><button type="button" onClick={onReset} className="mt-5 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground">Reset filters</button></div>;
}
