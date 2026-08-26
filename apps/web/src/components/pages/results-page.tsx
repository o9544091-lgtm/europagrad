"use client";
/* Scholarly Ledger style: sticky result controls, sortable evidence-led records, responsive table-to-card transformation, and clear recovery states. */
import { useMemo, useState } from 'react';
import Link from 'next/link';
import { Download, Eye, SlidersHorizontal, X, Database } from 'lucide-react';
import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { EmptyResults, ProgramTable } from '@/components/program-table';
import type { ProgramRow } from '@/lib/types';
import { exportPrograms, type ExportFormat } from '@/lib/export';

export default function ResultsPage({ rows, evidenceCounts }: { rows: ProgramRow[]; evidenceCounts: Record<string, number> }) {
  const [filters, setFilters] = useState<string[]>([]);
  const [sort, setSort] = useState<'score' | 'tuition' | 'deadline'>('score');
  const [showColumns, setShowColumns] = useState({ funding: true, language: true, work: true });

  const sorted = useMemo(() => [...rows].sort((a, b) => sort === 'score'
    ? (b.score ?? -1) - (a.score ?? -1)
    : sort === 'tuition'
      ? (a.tuitionEurPerYear ?? 999999) - (b.tuitionEurPerYear ?? 999999)
      : (a.daysRemaining ?? 9999) - (b.daysRemaining ?? 9999)), [rows, sort]);

  const removeFilter = (filter: string) => setFilters((items) => items.filter((item) => item !== filter));
  const reset = () => setFilters([]);

  return <div className="soft-enter"><div className="container py-8 lg:py-10"><div className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="data-label">Evidence ledger</p><h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">{rows.length} programme{rows.length === 1 ? '' : 's'}, ordered for review.</h1><p className="mt-3 text-sm leading-6 text-muted-foreground">Every record is drawn from verified research runs. Match scoring lands with the ranking engine.</p></div><div className="flex items-center gap-2"><DropdownMenu><DropdownMenuTrigger asChild><Button variant="outline" size="sm" className="gap-2" disabled={rows.length === 0}><Download className="h-3.5 w-3.5" />Export</Button></DropdownMenuTrigger><DropdownMenuContent align="end"><DropdownMenuLabel>Export {rows.length} programmes</DropdownMenuLabel><DropdownMenuSeparator />{(["xlsx", "csv", "json"] as ExportFormat[]).map((format) => <DropdownMenuCheckboxItem key={format} onSelect={() => exportPrograms(sorted, format, evidenceCounts)}>{format.toUpperCase()}</DropdownMenuCheckboxItem>)}</DropdownMenuContent></DropdownMenu></div></div>
    <div className="mt-6 flex flex-wrap items-center gap-2">{filters.map((filter) => <span key={filter} className="inline-flex items-center gap-1 rounded-md border border-primary/15 bg-primary/5 px-2.5 py-1.5 text-xs font-bold text-primary">{filter}<button type="button" aria-label={`Remove ${filter} filter`} onClick={() => removeFilter(filter)}><X className="h-3.5 w-3.5" /></button></span>)}{filters.length > 0 && <button type="button" onClick={() => setFilters([])} className="text-xs font-bold text-muted-foreground hover:text-foreground">Clear all</button>}</div>
  </div>
  <div className="sticky top-16 z-10 border-y border-border bg-card/95 backdrop-blur lg:top-16"><div className="container flex flex-wrap items-center gap-3 py-3"><div className="inline-flex items-center gap-2 text-sm font-bold"><SlidersHorizontal className="h-4 w-4 text-primary" />Sort by</div><div className="flex overflow-hidden rounded-lg border border-border bg-background"><button type="button" onClick={() => setSort('score')} className={`px-3 py-2 text-xs font-bold ${sort === 'score' ? 'bg-primary text-primary-foreground' : ''}`}>Score</button><button type="button" onClick={() => setSort('tuition')} className={`border-l border-border px-3 py-2 text-xs font-bold ${sort === 'tuition' ? 'bg-primary text-primary-foreground' : ''}`}>Tuition</button><button type="button" onClick={() => setSort('deadline')} className={`border-l border-border px-3 py-2 text-xs font-bold ${sort === 'deadline' ? 'bg-primary text-primary-foreground' : ''}`}>Deadline</button></div><DropdownMenu><DropdownMenuTrigger asChild><Button variant="ghost" size="sm" className="ml-auto gap-2"><Eye className="h-4 w-4" />Columns</Button></DropdownMenuTrigger><DropdownMenuContent align="end"><DropdownMenuLabel>Visible columns</DropdownMenuLabel><DropdownMenuSeparator />{(Object.keys(showColumns) as Array<keyof typeof showColumns>).map((column) => <DropdownMenuCheckboxItem key={column} checked={showColumns[column]} onCheckedChange={(checked) => setShowColumns((values) => ({ ...values, [column]: checked }))}>{column}</DropdownMenuCheckboxItem>)}</DropdownMenuContent></DropdownMenu></div></div>
  <div className="container py-7 pb-14">{rows.length === 0 ? <div className="ledger-card surface-dots flex min-h-72 flex-col items-center justify-center p-8 text-center"><Database className="h-7 w-7 text-primary" /><h3 className="mt-4 text-lg font-extrabold">No programmes researched yet</h3><p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">The database is empty. Run a research pass first — from the Actions tab (&quot;Research run&quot;) or locally via the agent CLI — then refresh this page.</p><Link href="/search" className="mt-5 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground">Configure a search</Link></div> : filters.length === 0 ? <ProgramTable rows={sorted} /> : <EmptyResults onReset={reset} />}</div>
  </div>;
}
