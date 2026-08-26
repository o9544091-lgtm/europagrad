"use client";
/* EuropaGrad style: a layered dark research terminal with compact indigo navigation, persistent saved-search context, and precise operational chrome. */
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState, type ReactNode } from 'react';
import { BarChart3, BookOpenCheck, ChevronRight, ClipboardList, FileText, Globe2, GraduationCap, Menu, Moon, Search, Sun, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { UserMenu } from '@/components/user-menu';
import { SearchHistory } from './search-history';

const navItems = [
  { href: '/', label: 'Explorer', icon: GraduationCap },
  { href: '/search', label: 'Search', icon: Search },
  { href: '/results', label: 'Results', icon: BarChart3 },
  { href: '/erasmus', label: 'Erasmus+', icon: Globe2 },
  { href: '/compare', label: 'Compare', icon: BookOpenCheck },
  { href: '/plan', label: 'My plan', icon: ClipboardList },
  { href: '/report', label: 'Report', icon: FileText },
];

const pageContexts: Array<{ prefix: string; label: string }> = [
  { prefix: '/search', label: 'Search protocol' }, { prefix: '/results', label: 'Sample match ledger' }, { prefix: '/programs', label: 'Programme dossier' }, { prefix: '/scholarships', label: 'Scholarship dossier' }, { prefix: '/countries', label: 'Country pack' }, { prefix: '/erasmus', label: 'Joint-programme register' }, { prefix: '/compare', label: 'Decision workbench' }, { prefix: '/plan', label: 'Application workflow' }, { prefix: '/report', label: 'Research output' }, { prefix: '/', label: 'Explorer' },
];

function isActive(pathname: string, href: string) {
  return href === '/' ? pathname === '/' : pathname.startsWith(href);
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [dark, setDark] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);
  const pageContext = pageContexts.find((item) => item.prefix === '/' ? pathname === '/' : pathname.startsWith(item.prefix))?.label ?? 'Explorer';

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-border bg-[#0D0F14]/95 px-4 py-5 backdrop-blur lg:flex lg:flex-col nocturne-rules">
        <Link href="/" className="mb-8 flex items-center gap-3 px-2 focus-visible:rounded-md">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary font-mono text-sm font-black text-primary-foreground" aria-hidden="true">EG</span>
          <span className="leading-tight"><span className="block text-sm font-extrabold tracking-tight">EuropaGrad</span><span className="block border-l border-primary/60 pl-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">Masters Explorer</span></span>
        </Link>
        <div className="mb-3 flex items-center justify-between border-y border-border py-2"><p className="data-label">Research rail</p><span className="tabular text-[10px] font-bold text-primary">01—09</span></div>
        <nav className="space-y-1" aria-label="Primary navigation">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors ${isActive(pathname, href) ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-secondary hover:text-foreground'}`}>
              <Icon className="h-4 w-4" aria-hidden="true" />{label}
            </Link>
          ))}
        </nav>
        <SearchHistory />
        <div className="mt-auto overflow-hidden rounded border border-border bg-secondary/35">
          <div className="oxblood-rule px-3 py-3"><p className="data-label">Saved-plan context</p><p className="mt-1 text-xs font-bold">3 sample choices in review</p></div>
          <div className="border-t border-border px-3 py-3"><p className="text-xs leading-5 text-muted-foreground">All entries are labelled sample data. Verify every application fact at source.</p><Link href="/report" className="mt-2 flex items-center gap-1 text-xs font-bold text-primary">Review source appendix <ChevronRight className="h-3.5 w-3.5" /></Link></div>
        </div>
      </aside>

      <header className="sticky top-0 z-20 border-b border-border bg-[#0D0F14]/90 backdrop-blur lg:ml-72">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2"><span className="grid h-8 w-8 place-items-center rounded-lg bg-primary font-mono text-xs font-black text-primary-foreground" aria-hidden="true">EG</span><span className="leading-tight"><span className="block text-sm font-extrabold">EuropaGrad</span><span className="block border-l border-primary/60 pl-1.5 text-[9px] font-bold uppercase tracking-[.15em] text-muted-foreground">Masters Explorer</span></span></Link>
          <div className="ml-2 hidden border-l border-border pl-4 lg:block"><p className="data-label">{pageContext}</p><p className="mt-0.5 text-xs font-semibold text-muted-foreground">Evidence-led programme research</p></div>
          <div className="ml-auto flex items-center gap-2">
            <UserMenu />
            <Link href="/plan" className="hidden rounded-md border border-border bg-card px-2.5 py-1.5 text-[11px] font-bold text-muted-foreground transition-colors hover:bg-secondary sm:inline-flex">Plan · 3</Link>
            <span className="hidden rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1.5 text-[10px] font-bold uppercase tracking-wide text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300 md:inline-flex">Sample data</span>
            <Button variant="ghost" size="icon" onClick={() => setDark((value) => !value)} aria-label="Toggle dark mode" className="rounded-lg">
              {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setMenuOpen((value) => !value)} aria-label="Toggle navigation menu" className="rounded-lg lg:hidden">
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
        {menuOpen && <nav className="border-t border-border bg-card px-4 py-3 lg:hidden" aria-label="Mobile navigation">{navItems.map(({ href, label, icon: Icon }) => <Link onClick={() => setMenuOpen(false)} key={href} href={href} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold ${isActive(pathname, href) ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}><Icon className="h-4 w-4" />{label}</Link>)}</nav>}
      </header>
      <main className="lg:ml-72">{children}</main>
    </div>
  );
}
