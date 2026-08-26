"use client";
/* EuropaGrad style: compact semantic stamps on layered dark surfaces, using indigo for match/selection and clear funding and deadline semantics. */
import type { DeadlineStatus, FundingClass, MatchClass } from '@/lib/types';
import { deadlineStatusLabels, fundingClassLabels } from '@/lib/mock-data';

const deadlineStyles: Record<DeadlineStatus, string> = {
  OPEN: 'border-emerald-900 bg-emerald-950/40 text-emerald-300',
  APPROACHING: 'border-amber-900 bg-amber-950/40 text-amber-300',
  NOT_YET_OPEN: 'border-sky-900 bg-sky-950/40 text-sky-300',
  CLOSED: 'border-red-900 bg-red-950/40 text-red-300',
  FUTURE_NOT_PUBLISHED: 'border-stone-600 bg-transparent text-stone-300',
  UNKNOWN: 'border-stone-600 bg-transparent text-stone-400',
};

const fundingStyles: Record<FundingClass, string> = {
  FULLY_FUNDED: 'bg-emerald-600 text-white', FULLY_FUNDED_STIPEND: 'bg-emerald-700 text-white', TUITION_FREE: 'bg-primary text-primary-foreground', TUITION_WAIVER: 'bg-indigo-950 text-indigo-200', PARTIAL_SCHOLARSHIP: 'bg-amber-950 text-amber-200', LOW_TUITION: 'bg-sky-950 text-sky-200', SELF_FUNDED: 'bg-zinc-700 text-zinc-100', RESEARCH_FUNDED: 'bg-violet-950 text-violet-200', ASSISTANTSHIP: 'bg-cyan-950 text-cyan-200', NOT_SPECIFIED: 'bg-zinc-800 text-zinc-300',
};

const matchStyles: Record<MatchClass, string> = { HIGH: 'border border-primary/40 bg-primary/15 text-indigo-200', POSSIBLE: 'border border-zinc-700 bg-zinc-800 text-zinc-200', LOW: 'border border-red-900 bg-red-950/45 text-red-300', UNKNOWN: 'border border-zinc-700 bg-transparent text-zinc-400' };

export const deadlineStripClass: Record<DeadlineStatus, string> = {
  OPEN: 'border-l-emerald-600', APPROACHING: 'border-l-amber-500', NOT_YET_OPEN: 'border-l-blue-600', FUTURE_NOT_PUBLISHED: 'border-l-slate-400', CLOSED: 'border-l-red-600', UNKNOWN: 'border-l-slate-400',
};

export function DeadlineBadge({ status, days }: { status: DeadlineStatus; days?: number | null }) {
  return <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-md border px-2 py-1 text-[11px] font-bold ${deadlineStyles[status]}`}>{deadlineStatusLabels[status]}{typeof days === 'number' && days > 0 ? <span className="tabular opacity-80">· {days}d</span> : null}</span>;
}

export function FundingBadge({ funding }: { funding: FundingClass }) {
  return <span className={`inline-flex rounded-md px-2 py-1 text-[11px] font-bold leading-none ${fundingStyles[funding]}`}>{fundingClassLabels[funding]}</span>;
}

export function MatchPill({ match }: { match: MatchClass }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold ${matchStyles[match]}`}>{match === 'HIGH' ? 'High match' : match === 'POSSIBLE' ? 'Possible' : match === 'LOW' ? 'Low match' : 'Unknown'}</span>;
}
