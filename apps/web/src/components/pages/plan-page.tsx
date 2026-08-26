"use client";
/* EuropaGrad plan: real shortlist + tracker board persisted per account via RLS. */
import Link from 'next/link';
import { ArrowUpRight, CalendarDays, LockKeyhole, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DeadlineBadge, FundingBadge } from '@/components/status-badge';
import { openAuthDialog } from '@/components/auth-dialog';
import { STAGE_LABELS, TRACKER_STAGES, usePlan, type PlanProgram } from '@/components/plan/use-plan';

function daysTo(deadline: string | null) {
  if (!deadline) return null;
  const d = new Date(deadline);
  return Number.isNaN(d.getTime()) ? null : Math.ceil((d.getTime() - Date.now()) / 86_400_000);
}

function ProgramCard({ program, action }: { program: PlanProgram; action?: React.ReactNode }) {
  const days = daysTo(program.deadline);
  return <div className="rounded-lg border border-border p-4 transition-colors hover:bg-secondary/50"><div className="flex items-start justify-between gap-3"><div><p className="font-bold">{program.name}</p><p className="mt-1 text-xs text-muted-foreground">{program.university} · {program.country}</p></div>{action}</div><div className="mt-3 flex flex-wrap items-center gap-2"><FundingBadge funding={program.fundingClass as never} /><DeadlineBadge status={program.deadlineStatus as never} days={days} /></div></div>;
}

export default function PlanPage() {
  const { data, authRequired, loading, refresh, saveItem, removeSaved, setTrackerStatus, removeTracker } = usePlan();

  const savedPrograms = (data?.saved ?? []).filter((item) => item.entityType === 'PROGRAM' && item.program);
  const tracker = data?.tracker ?? [];
  const trackedIds = new Set(tracker.map((entry) => entry.programId));
  const untracked = savedPrograms.filter((item) => item.program && !trackedIds.has(item.program.id));

  async function addToTracker(programId: string) {
    if (await setTrackerStatus(programId, 'INTERESTED')) await refresh();
  }

  async function moveStage(programId: string, stage: string) {
    if (stage === 'REMOVE') { if (await removeTracker(programId)) await refresh(); return; }
    if (await setTrackerStatus(programId, stage)) await refresh();
  }

  async function removeFromShortlist(entityId: string) {
    if (await removeSaved('PROGRAM', entityId)) await refresh();
  }

  return <div className="container soft-enter py-8 pb-14 lg:py-10"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="data-label">Application workflow</p><h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">My plan, modelled as a decision queue.</h1><p className="mt-3 text-sm leading-6 text-muted-foreground">Saved programmes and application stages, synced to your account.</p></div></div>
    {authRequired && <div className="mt-7 rounded-xl border border-primary/20 bg-primary/[0.04] p-5"><div className="flex gap-3"><LockKeyhole className="mt-0.5 h-5 w-5 text-primary" /><div><p className="font-extrabold">Sign in to save a real plan</p><p className="mt-1 text-sm leading-6 text-muted-foreground">A free account keeps your shortlist and application queue synced across devices. Browsing results stays open to everyone.</p><Button variant="outline" size="sm" className="mt-4" onClick={openAuthDialog}>Sign in with email link</Button></div></div></div>}
    {!authRequired && loading && <p className="mt-8 text-sm text-muted-foreground">Loading your plan…</p>}
    {!authRequired && !loading && <div className="mt-7 grid gap-5 xl:grid-cols-[340px_1fr]"><aside className="space-y-4"><div className="ledger-card p-5"><p className="data-label">Shortlist · {savedPrograms.length}</p><div className="mt-4 space-y-3">{savedPrograms.length === 0 ? <p className="text-sm leading-6 text-muted-foreground">Nothing saved yet. Open any programme and press “Add to plan”.</p> : savedPrograms.map((item) => item.program && <ProgramCard key={item.entityId} program={item.program} action={<button type="button" aria-label="Remove from shortlist" onClick={() => void removeFromShortlist(item.entityId)} className="text-muted-foreground hover:text-destructive"><Trash2 className="h-4 w-4" /></button>} />)}</div></div>
      {untracked.length > 0 && <div className="ledger-card p-5"><p className="data-label">Add to queue</p><div className="mt-3 space-y-2">{untracked.map((item) => item.program && <button key={item.program.id} type="button" onClick={() => void addToTracker(item.program!.id)} className="flex w-full items-center justify-between gap-2 rounded-lg border border-border px-3 py-2 text-left text-sm font-semibold transition-colors hover:bg-secondary/50"><span className="truncate">{item.program.name}</span><Plus className="h-4 w-4 shrink-0 text-primary" /></button>)}</div></div>}
      <div className="rounded-xl border border-primary/20 bg-primary/[0.04] p-5 text-sm leading-6 text-muted-foreground"><p className="font-extrabold text-foreground">Deadlines move.</p>Scholarship and admission calendars are separate. Re-verify every date at its official source before applying.</div></aside>
      <section className="overflow-x-auto"><div className="mb-3 flex min-w-[1060px] items-center justify-between border-b border-border pb-3"><div><p className="data-label">Application queue ledger</p><p className="mt-1 text-xs text-muted-foreground">Each stage keeps a visible funding and deadline signal.</p></div><span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-primary">{tracker.length} tracked</span></div><div className="flex min-w-[1060px] gap-3">{TRACKER_STAGES.map((stage, stageIndex) => { const items = tracker.filter((entry) => stage === 'RESULT' ? ['ADMISSION_RECEIVED', 'ACCEPTED', 'REJECTED'].includes(entry.status) : entry.status === stage); return <div key={stage} className="w-44 shrink-0"><div className="mb-3 border-l-2 border-primary bg-secondary px-3 py-3"><div className="flex items-center justify-between gap-2"><span className="text-xs font-extrabold">{STAGE_LABELS[stage]}</span><span className="rounded-full bg-card px-2 py-0.5 tabular text-[11px] font-bold text-muted-foreground">{items.length}</span></div><p className="mt-1 text-[10px] font-bold uppercase tracking-[.12em] text-muted-foreground">Stage 0{stageIndex + 1}</p></div><div className="min-h-[300px] space-y-3 rounded-lg border border-dashed border-border bg-secondary/20 p-2">{items.length === 0 ? <div className="grid min-h-24 place-items-center p-3 text-center text-xs leading-5 text-muted-foreground">Nothing here yet.</div> : items.map((entry) => entry.program && <div key={entry.programId} className="overflow-hidden rounded-lg border border-border bg-card shadow-sm"><div className="border-l-2 border-primary px-3 pt-3"><p className="text-xs font-extrabold leading-5">{entry.program.name}</p><p className="mt-1 text-[11px] leading-4 text-muted-foreground">{entry.program.university}</p></div><div className="mt-3 flex items-center justify-between border-t border-border bg-secondary/45 px-3 py-2"><span className="tabular text-[10px] font-bold text-primary">{entry.program.deadline ? `${daysTo(entry.program.deadline) ?? '—'}d` : '—'}</span><div className="flex items-center gap-1"><Link href={`/programs/${entry.programId}`} aria-label="Open dossier" className="text-muted-foreground hover:text-primary"><ArrowUpRight className="h-3.5 w-3.5" /></Link><select value={entry.status} onChange={(event) => void moveStage(entry.programId, event.target.value)} aria-label="Move stage" className="rounded bg-background text-[10px] font-bold">{TRACKER_STAGES.filter((s) => s !== 'RESULT').map((s) => <option key={s} value={s}>{STAGE_LABELS[s]}</option>)}{['ADMISSION_RECEIVED', 'ACCEPTED', 'REJECTED'].map((s) => <option key={s} value={s}>{s.replaceAll('_', ' ').toLowerCase()}</option>)}</select><button type="button" aria-label="Remove from tracker" onClick={() => void moveStage(entry.programId, 'REMOVE')} className="text-muted-foreground hover:text-destructive"><Trash2 className="h-3 w-3" /></button></div></div></div>)}</div></div>; })}</div></section></div>}
  </div>;
}
