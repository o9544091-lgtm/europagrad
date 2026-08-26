"use client";
/* Scholarly Ledger style: side-by-side decision ledger that exposes trade-offs instead of reducing choices to a single opaque score. */
import { useMemo, useState } from 'react';
import Link from 'next/link';
import { Check, Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DeadlineBadge, FundingBadge, MatchPill } from '@/components/status-badge';
import { programs } from '@/lib/mock-data';
import type { ProgramRow } from '@/lib/types';

function valueTuition(program: ProgramRow) { return program.tuitionEurPerYear === null ? '—' : program.tuitionEurPerYear === 0 ? '€0' : `€${program.tuitionEurPerYear.toLocaleString('en-US')}`; }

export default function ComparePage() {
  const [ids, setIds] = useState(['erasmus-big-data', 'tu-berlin-cs', 'paris-saclay-data']);
  const selected = useMemo(() => ids.map((id) => programs.find((program) => program.id === id)).filter((program): program is ProgramRow => Boolean(program)), [ids]);
  const add = () => { const candidate = programs.find((program) => !ids.includes(program.id)); if (candidate && ids.length < 4) setIds((items) => [...items, candidate.id]); };
  const rows: Array<{ label: string; get: (program: ProgramRow) => React.ReactNode; best?: (program: ProgramRow) => boolean }> = [
    { label: 'Funding', get: (p) => <FundingBadge funding={p.fundingClass} />, best: (p) => p.fundingClass === 'FULLY_FUNDED' || p.fundingClass === 'FULLY_FUNDED_STIPEND' },
    { label: 'Tuition / year', get: (p) => valueTuition(p), best: (p) => p.tuitionEurPerYear === 0 },
    { label: 'Linked stipend', get: (p) => p.scholarshipName ?? '—' },
    { label: 'Language / MOI', get: (p) => `${p.language} · ${p.moiAccepted === true ? 'MOI signal' : 'verify MOI'}` },
    { label: 'Deadline', get: (p) => <DeadlineBadge status={p.deadlineStatus} days={p.daysRemaining} />, best: (p) => p.deadlineStatus === 'OPEN' },
    { label: 'Part-time', get: (p) => p.partTimeWork.replaceAll('_', ' ').toLowerCase() },
    { label: 'Living cost context', get: (p) => p.country === 'Germany' ? '€850–1,150 sample' : p.country === 'France' ? '€900–1,350 sample' : p.country === 'Sweden' ? '€900–1,250 sample' : 'Varies by city' },
    { label: 'Match', get: (p) => p.matchClass ? <MatchPill match={p.matchClass} /> : <span className='text-xs text-muted-foreground'>—</span>, best: (p) => p.matchClass === 'HIGH' },
    { label: 'Score', get: (p) => <span className="tabular text-xl font-extrabold text-primary">{p.score ?? '—'}</span>, best: (p) => p.score != null && p.score === Math.max(...selected.map((candidate) => candidate.score ?? -1)) },
  ];
  return <div className="container soft-enter py-8 pb-14 lg:py-10"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="data-label">Decision workbench</p><h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">Compare a shortlist without losing context.</h1><p className="mt-3 text-sm leading-6 text-muted-foreground">Up to four sample programmes. Best-in-row highlights describe a visible criterion, not an overall recommendation.</p></div><Button variant="outline" onClick={add} disabled={ids.length === 4} className="gap-2"><Plus className="h-4 w-4" />Add sample programme</Button></div>
    <div className="mt-7 overflow-x-auto rounded-xl border border-border bg-card"><table className="w-full min-w-[760px] text-left"><thead><tr className="border-b border-border bg-secondary/40"><th className="w-44 px-4 py-4 text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Decision field</th>{selected.map((program) => <th key={program.id} className="min-w-52 border-l border-border px-4 py-4 align-top"><div className="flex items-start justify-between gap-3"><Link href={`/programs/${program.id}`} className="font-extrabold hover:text-primary">{program.university}</Link><button type="button" onClick={() => setIds((items) => items.filter((id) => id !== program.id))} aria-label={`Remove ${program.program} from comparison`}><X className="h-4 w-4 text-muted-foreground" /></button></div><p className="mt-1 text-xs font-medium text-muted-foreground">{program.program}</p></th>)}</tr></thead><tbody>{rows.map((row) => <tr key={row.label} className="ledger-row"><td className="px-4 py-4 text-sm font-bold">{row.label}</td>{selected.map((program) => <td key={program.id} className={`border-l border-border px-4 py-4 text-sm ${row.best?.(program) ? 'bg-emerald-50/70 dark:bg-emerald-950/20' : ''}`}><div className="flex items-center gap-2">{row.get(program)}{row.best?.(program) && <Check className="h-4 w-4 text-emerald-700 dark:text-emerald-400" aria-label="Best shown for this field" />}</div></td>)}</tr>)}</tbody></table></div>
    <div className="mt-5 rounded-xl border border-primary/20 bg-primary/[0.04] p-4 text-sm leading-6 text-muted-foreground"><strong className="text-foreground">Interpretation note.</strong> A comparison clarifies trade-offs, but the sample score must not be treated as a prediction of admission, funding, visa, or employment outcomes.</div>
  </div>;
}
