"""Task 11 live dry-run: 2 real Italian universities → cited records in staging DB.

Real fetch chain (registry dump → sitemaps → adaptive static fetch) + a heuristic
extractor that builds CitedValue fields from verbatim sentences in the fetched
text (validated by ExtractionValidator, same gate the LLM path uses). Runs twice
to prove idempotency: second run must UPDATE, not duplicate.

Usage (from apps/agent):  uv run python ../../scripts/dry_run_orchestrator.py
Requires: SUPABASE_URL + SUPABASE_SERVICE_KEY in .env; network. No LLM/search keys.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "agent" / "src"))

from selectolax.parser import HTMLParser  # noqa: E402

from europagrad_agent.engines.router import AdaptiveRouter  # noqa: E402
from europagrad_agent.engines.static import StaticEngine  # noqa: E402
from europagrad_agent.extraction.schemas import (  # noqa: E402
    CitedValue,
    ExtractionBundle,
    ExtractionValidator,
    ProgramExtraction,
)
from europagrad_agent.pipelines.orchestrator import ResearchOrchestrator  # noqa: E402
from europagrad_agent.registries.depth import get_profile  # noqa: E402
from europagrad_agent.registries.ror_dump import RorDumpLoader  # noqa: E402
from europagrad_agent.registries.sitemap import SitemapHarvester  # noqa: E402
from europagrad_agent.storage.domain_stats import MemoryDomainStats  # noqa: E402
from europagrad_agent.storage.job_progress import MemoryJobProgress  # noqa: E402
from europagrad_agent.storage.universities import UniversityStore  # noqa: E402
from europagrad_agent.storage.writer import ProgramWriter  # noqa: E402

TARGET_UNIVERSITIES = ("Politecnico di Milano", "University of Bologna")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if 20 < len(s.strip()) < 300]


def find_sentence(sent: list[str], pattern: str) -> tuple[str, str] | None:
    for s in sent:
        m = re.search(pattern, s, re.IGNORECASE)
        if m:
            return m.group(1) if m.groups() else m.group(0), s
    return None


def html_to_text(html: str) -> str:
    tree = HTMLParser(html)
    for node in tree.css("script, style, nav, header, footer"):
        node.decompose()
    return re.sub(r"\s+", " ", tree.body.text(separator=" ", strip=True) if tree.body else "")


class HeuristicExtractor:
    """Builds cited values from verbatim sentences in the fetched page.
    Same contract as the LLM path: quotes must survive ExtractionValidator."""

    name = "HEURISTIC"

    async def extract(self, url: str, page_text: str, target: str = "program"):
        text = html_to_text(page_text)
        if len(text) < 300:
            bundle = ExtractionBundle(program=ProgramExtraction(source_url=url))
            return ExtractionValidator.validate(bundle, text)

        sent = sentences(text)
        fields: dict = {"source_url": url}

        h1 = None
        try:
            node = HTMLParser(page_text).css_first("h1")
            h1 = node.text(strip=True) if node else None
        except Exception:
            h1 = None
        if h1 and 5 < len(h1) < 120 and h1 in text:
            fields["program_name"] = CitedValue(value=h1.strip(), source_url=url, quote=h1.strip())

        ielts = find_sentence(sent, r"IELTS[^.\d]{0,20}(\d\.\d)")
        if ielts:
            fields["ielts_overall"] = CitedValue(value=float(ielts[0]), source_url=url, quote=ielts[1][:200])

        duration = find_sentence(sent, r"(\d{1,2})\s+(?:months|month)")
        if duration:
            fields["duration_months"] = CitedValue(value=int(duration[0]), source_url=url, quote=duration[1][:200])

        tuition = find_sentence(sent, r"(?:EUR|€)\s*([\d.,]{3,12})")
        if tuition:
            amount = float(tuition[0].replace(".", "").replace(",", "")) if "," in tuition[0] else float(tuition[0])
            fields["tuition_eur_per_year"] = CitedValue(
                value={"amount_eur": amount, "note": "heuristic pass"},
                source_url=url, quote=tuition[1][:200],
            )

        deadline = find_sentence(sent, r"deadline[:\s]+([^.;]{6,40})")
        if deadline:
            fields["application_deadline"] = CitedValue(value=deadline[0].strip(), source_url=url, quote=deadline[1][:200])

        for tag, pat in (("cs", r"computer science"), ("ai", r"artificial intelligence"), ("data-science", r"data science")):
            if re.search(pat, text, re.IGNORECASE):
                fields.setdefault("field_tags", []).append(tag)

        bundle = ExtractionBundle(program=ProgramExtraction.model_validate(fields))
        return ExtractionValidator.validate(bundle, text)


async def main() -> None:
    profile = get_profile("L2")
    inventory = RorDumpLoader()
    all_it = await inventory.load_country("IT")
    targets = [
        i for i in all_it
        if any(t.lower() in i.name.lower() for t in TARGET_UNIVERSITIES) and i.domain
    ][:2]
    if len(targets) < 2:
        print(f"only found {len(targets)} target universities: {[i.name for i in targets]}")
        sys.exit(1)
    print(f"targets: {[(i.name, i.domain) for i in targets]}")

    static = StaticEngine()
    router = AdaptiveRouter(static=static, stats=MemoryDomainStats())
    harvester = SitemapHarvester()
    store_universities = UniversityStore()
    writer = ProgramWriter()
    progress = MemoryJobProgress(["IT"], "L2-dry")

    for attempt in (1, 2):
        orch = ResearchOrchestrator(
            router=router, harvester=harvester, inventory=FakeSingle(targets),
            extractor=HeuristicExtractor(), store=CombinedStore(store_universities, writer),
            progress_cb=progress.update,
        )
        summary = await orch.run(["IT"], depth=profile, write=True, university_limit=2, candidate_limit=6)
        print(f"--- run {attempt}: fetched={summary.pages_fetched} extracted={summary.pages_extracted} "
              f"created={summary.programs_written} updated={summary.programs_updated} "
              f"qc_warn={summary.qc_warnings} qc_err={summary.qc_errors}")
        for note in summary.notes[:6]:
            print(f"    note: {note[:110]}")

    if attempt == 2 and summary.programs_written > 0:
        print("IDEMPOTENCY FAILED: second run created new programs")
        sys.exit(2)
    print("IDEMPOTENCY OK: second run only updated")


class FakeSingle:
    def __init__(self, institutions) -> None:
        self._institutions = institutions

    async def load_country(self, iso2: str) -> list:
        return list(self._institutions)


class CombinedStore:
    def __init__(self, universities: UniversityStore, writer: ProgramWriter) -> None:
        self._universities = universities
        self._writer = writer

    async def ensure_university(self, institution) -> str:
        return await self._universities.ensure_university(institution)

    async def get_university_id(self, institution) -> str | None:
        return await self._universities.get_university_id(institution)

    async def upsert_program(self, university_id: str, bundle) -> dict:
        return await self._writer.upsert_program(university_id, bundle)


if __name__ == "__main__":
    asyncio.run(main())
