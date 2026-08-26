"""CLI entry point for the EuropaGrad agent.

Scaffold (task 1): subcommands validate environment and print execution plans.
The run pipeline itself is implemented by tasks 6-13 (see docs/tasks.md).
"""

import argparse
import sys

from rich.console import Console
from rich.table import Table

from europagrad_agent import __version__
from europagrad_agent.config import get_settings

console = Console()

SEED_COUNTRIES = ["DE", "IT", "FR", "NL", "SE"]

ALL_COUNTRIES = [
    "AT", "BE", "BG", "CH", "CY", "CZ", "DE", "DK", "EE", "ES",
    "FI", "FR", "GR", "HR", "HU", "IE", "IS", "IT", "LT", "LU",
    "LV", "MT", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK",
] + ["AU", "US"]


def cmd_doctor(args: argparse.Namespace) -> int:
    settings = get_settings()
    rows: list[tuple[str, bool, str]] = [
        ("SUPABASE_URL / SUPABASE_SERVICE_KEY", bool(settings.supabase_url and settings.supabase_service_key), "writes to dataset"),
        ("OPENROUTER_API_KEY", bool(settings.openrouter_api_key), "LLM extraction"),
        ("TAVILY_API_KEY", bool(settings.tavily_api_key), "search discovery"),
    ]
    table = Table(title=f"europagrad agent {__version__} — environment")
    table.add_column("Setting")
    table.add_column("Present", justify="center")
    table.add_column("Needed for")
    for name, present, purpose in rows:
        table.add_row(name, "[green]yes[/green]" if present else "[red]no[/red]", purpose)
    console.print(table)
    missing = [name for name, present, _ in rows if not present]
    if missing:
        console.print(f"[yellow]Missing:[/yellow] {', '.join(missing)} — copy .env.example to apps/agent/.env")
        return 1
    return 0


def cmd_countries(args: argparse.Namespace) -> int:
    table = Table(title="Supported countries")
    table.add_column("Code")
    table.add_column("Launch seed")
    for code in ALL_COUNTRIES:
        marker = "[green]seed[/green]" if code in SEED_COUNTRIES else ""
        table.add_row(code, marker)
    console.print(table)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    codes = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
    unknown = [c for c in codes if c not in ALL_COUNTRIES]
    if unknown:
        console.print(f"[red]Unsupported country codes:[/red] {', '.join(unknown)}")
        return 2
    if args.depth not in {"L1", "L2", "L3"}:
        console.print("[red]Depth must be L1, L2, or L3[/red]")
        return 2

    doctor_code = cmd_doctor(args)
    if doctor_code != 0 and not args.dry_run:
        return doctor_code

    console.print("\n[bold]Execution plan[/bold]")
    console.print(f"  countries : {', '.join(codes)}")
    console.print(f"  depth     : {args.depth}")
    caps = {"L1": ("3 search pages", "portals only", 15), "L2": ("6 search pages", "all universities", 40), "L3": ("10 search pages", "full sitemaps", 100)}
    pages, sitemaps, page_cap = caps[args.depth]
    console.print(f"  caps      : {pages}, sitemap harvest: {sitemaps}, per-domain page cap: {page_cap}")
    console.print(f"  mode      : {'DRY RUN (no crawl, no writes)' if args.dry_run else 'REAL RUN'}")

    if not args.dry_run:
        import asyncio

        from europagrad_agent.pipelines.run_real import execute_real_run

        try:
            summary = asyncio.run(
                execute_real_run(
                    countries=codes,
                    depth_level=args.depth,
                    extractor_kind=getattr(args, "extractor", "auto"),
                    university_limit=(args.limit if getattr(args, "limit", 0) else None),
                    candidate_limit=getattr(args, "candidate_limit", 8),
                    job_id=getattr(args, "job_id", None) or None,
                )
            )
            console.print("\n[bold]Run complete[/bold]")
            console.print(f"  universities : {summary['universities']}")
            console.print(f"  pages fetched: {summary['pages_fetched']}")
            console.print(f"  extracted    : {summary['pages_extracted']}")
            console.print(f"  created      : {summary['programs_written']}")
            console.print(f"  updated      : {summary['programs_updated']}")
            console.print(f"  qc warnings  : {summary['qc_warnings']}")
            console.print(f"  qc errors    : {summary['qc_errors']}")
            for note in summary["notes"][:8]:
                console.print(f"  note: {note[:110]}")
            return 0
        except Exception as err:
            console.print(f"[red]Run failed:[/red] {err}")
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent", description="EuropaGrad research agent CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="check required API keys").set_defaults(func=cmd_doctor)
    sub.add_parser("countries", help="list supported countries").set_defaults(func=cmd_countries)

    run = sub.add_parser("run", help="plan/execute a research run")
    run.add_argument("--countries", required=True, help='comma-separated ISO codes, e.g. "IT,DE"')
    run.add_argument("--depth", default="L2", help="L1 | L2 | L3 (default L2)")
    run.add_argument("--dry-run", action="store_true", help="print plan without crawling/writing")
    run.add_argument("--extractor", default="auto", choices=["auto", "llm", "heuristic"], help="extraction path (default auto)")
    run.add_argument("--limit", type=int, default=None, help="cap universities processed (per run)")
    run.add_argument("--candidate-limit", type=int, default=8, help="cap candidate pages per university")
    run.add_argument("--job-id", default=None, help="attach to an existing research_jobs row (set by app trigger)")
    run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
