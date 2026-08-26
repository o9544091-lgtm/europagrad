"use client";
/* Scholarly Ledger style: country research pack with cost signals and the local programme ledger. */
import Link from 'next/link';
import { ArrowLeft, ArrowUpRight, BriefcaseBusiness, CircleDollarSign, Landmark } from 'lucide-react';
import { ProgramTable } from '@/components/program-table';
import type { ProgramRow } from '@/lib/types';
import type { CountryPageData } from '@/lib/programs-query';

interface Pack {
  tuitionNorms?: string;
  livingCostMonthlyEur?: { low?: number; avg?: number };
  partTimeRules?: string;
  majorScholarships?: string[];
  applicationPlatform?: string;
}

function flagFromCode(code: string) {
  if (!/^[A-Za-z]{2}$/.test(code)) return '';
  return String.fromCodePoint(...code.toUpperCase().split('').map((c) => 0x1f1e6 + c.charCodeAt(0) - 65));
}

function Stat({ icon: Icon, label, value }: { icon: typeof CircleDollarSign; label: string; value: string }) { return <div className="ledger-card p-5"><Icon className="h-5 w-5 text-primary" /><p className="mt-5 data-label">{label}</p><p className="mt-1 text-sm font-bold leading-6">{value}</p></div>; }

export default function CountryPage({ country, programs }: { country: CountryPageData['country']; programs: ProgramRow[] }) {
  if (!country) return <div className="container py-12"><h1 className="text-2xl font-extrabold">Country pack not found</h1><Link href="/search" className="mt-4 inline-flex text-sm font-bold text-primary">Return to search</Link></div>;

  const flag = flagFromCode(country.id);
  const pack = (country.pack ?? {}) as Pack;
  const living = pack.livingCostMonthlyEur;

  return <div className="soft-enter"><section className="relative overflow-hidden border-b border-border bg-card"><div className="absolute inset-0 bg-gradient-to-br from-primary/[0.07] via-transparent to-accent/[0.06]" /><div className="container relative py-7 pb-12 lg:py-10 lg:pb-16"><Link href="/search" className="inline-flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-primary"><ArrowLeft className="h-4 w-4" />Back to search</Link><div className="mt-8 flex items-center gap-3"><span className="text-4xl" role="img" aria-label={country.name}>{flag}</span><p className="data-label">Country pack · {programs.length} researched programme{programs.length === 1 ? '' : 's'}</p></div><h1 className="mt-3 text-4xl font-extrabold tracking-tight">{country.name}</h1>{!country.researched && <p className="mt-4 max-w-xl rounded-lg border border-border bg-secondary/40 px-4 py-3 text-sm leading-6 text-muted-foreground">The deep country pack (tuition norms, scholarship ecosystem, work rules) has not been researched yet — queue a research pass to populate it. Programmes below come from completed runs.</p>}</div></section>
  <div className="container py-8 pb-14"><div className="grid gap-4 md:grid-cols-3"><Stat icon={CircleDollarSign} label="Tuition norms" value={pack.tuitionNorms ?? 'Not researched yet'} /><Stat icon={Landmark} label="Living cost · monthly est." value={living?.avg ? `€${living.low ?? '?'} low · €${living.avg} average` : 'Not researched yet'} /><Stat icon={BriefcaseBusiness} label="Part-time rules" value={pack.partTimeRules ?? 'Not researched yet'} /></div>
    <section className="mt-8 grid gap-5 lg:grid-cols-[1fr_.8fr]"><div className="ledger-card p-5"><p className="data-label">Scholarship ecosystem</p><div className="mt-4 space-y-3">{(pack.majorScholarships ?? []).length === 0 ? <p className="text-sm leading-6 text-muted-foreground">Not researched yet — queue a research pass for this country.</p> : pack.majorScholarships!.map((item) => <div key={item} className="flex items-center justify-between rounded-lg border border-border bg-secondary/30 px-4 py-3"><span className="text-sm font-bold">{item}</span><ArrowUpRight className="h-4 w-4 text-primary" /></div>)}</div><p className="mt-5 text-xs leading-5 text-muted-foreground">Scholarship availability changes by year and applicant route — always verify at source.</p></div><div className="ledger-card p-5"><p className="data-label">Research timeline notes</p><ol className="mt-4 space-y-5 border-l border-primary/30 pl-5"><li><p className="text-sm font-bold">First pass · 4–8 months out</p><p className="mt-1 text-xs leading-5 text-muted-foreground">Use {pack.applicationPlatform ?? 'the national application portal'} and programme pages to map proof requirements.</p></li><li><p className="text-sm font-bold">Funding pass · before course deadlines</p><p className="mt-1 text-xs leading-5 text-muted-foreground">Separate scholarship calendars from admission calendars; they may not align.</p></li><li><p className="text-sm font-bold">Visa pass · after offers</p><p className="mt-1 text-xs leading-5 text-muted-foreground">Confirm document, insurance, and funds requirements with official authorities.</p></li></ol></div></section>
    <section className="mt-8"><div className="mb-5 flex items-end justify-between"><div><p className="data-label">Local ledger</p><h2 className="mt-1 text-xl font-extrabold">Researched programmes</h2></div><Link href="/results" className="text-sm font-bold text-primary">Full results</Link></div>{programs.length === 0 ? <div className="ledger-card p-8 text-center text-sm text-muted-foreground">No programmes researched for {country.name} yet — queue a research pass.</div> : <ProgramTable rows={programs.slice(0, 10)} compact />}</section></div></div>;
}
