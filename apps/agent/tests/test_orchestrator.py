"""Task 11 tests: orchestrator flow, QC gate, idempotent store semantics."""

from __future__ import annotations

import httpx

from europagrad_agent.engines.router import AdaptiveRouter
from europagrad_agent.engines.static import StaticEngine
from europagrad_agent.extraction.schemas import (
    CitedValue,
    ExtractionBundle,
    ProgramExtraction,
)
from europagrad_agent.pipelines.orchestrator import ResearchOrchestrator
from europagrad_agent.pipelines.qc import check_program
from europagrad_agent.registries.depth import get_profile
from europagrad_agent.registries.ror import Institution
from europagrad_agent.registries.sitemap import SitemapHarvester
from europagrad_agent.storage.domain_stats import MemoryDomainStats
from europagrad_agent.storage.job_progress import MemoryJobProgress
from html_fixtures import PROGRAM_HTML

PAGE_TEXT = (
    "MSc Computer Science. The programme is taught entirely in English and takes 24 months to "
    "complete. IELTS 6.5 overall with no band below 6.0 is required."
)


def inst(name: str = "Test University", domain: str | None = "test.edu") -> Institution:
    return Institution(name=name, country="EE", domain=domain, ror_id="https://ror.org/x")


def cited(value, quote: str) -> CitedValue:
    return CitedValue(value=value, source_url="https://test.edu/msc", quote=quote)


def good_bundle(name: str = "MSc Computer Science") -> ExtractionBundle:
    return ExtractionBundle(
        program=ProgramExtraction(
            source_url="https://test.edu/msc",
            program_name=cited(name, "MSc Computer Science"),
            duration_months=cited(24, "takes 24 months to"),
            field_tags=["cs"],
        )
    )


class FakeInventory:
    def __init__(self, institutions: list[Institution]) -> None:
        self._institutions = institutions

    async def load_country(self, iso2: str) -> list[Institution]:
        return list(self._institutions)


class FakeExtractor:
    def __init__(self, bundles: list[ExtractionBundle]) -> None:
        self._bundles = list(bundles)
        self.calls: list[str] = []

    async def extract(self, url: str, page_text: str, target: str = "program"):
        self.calls.append(url)
        return self._bundles.pop(0), []


class MemoryStore:
    def __init__(self) -> None:
        self.universities: dict[str, str] = {}
        self.programs: dict[tuple, dict] = {}
        self.upserts = 0

    async def ensure_university(self, institution: Institution) -> str:
        key = institution.name
        if key not in self.universities:
            self.universities[key] = f"uid-{len(self.universities) + 1}"
        return self.universities[key]

    async def get_university_id(self, institution: Institution) -> str | None:
        return self.universities.get(institution.name)

    async def upsert_program(self, university_id: str, bundle: ExtractionBundle) -> dict:
        self.upserts += 1
        key = (university_id, bundle.program.program_name.value.lower())
        if key not in self.programs:
            self.programs[key] = {"id": f"pid-{len(self.programs) + 1}", "created": True}
            return {"program_id": self.programs[key]["id"], "created": True, "changed_fields": []}
        return {"program_id": self.programs[key]["id"], "created": False, "changed_fields": ["tuition"]}


def make_harvester(urls: list[str]) -> SitemapHarvester:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\nCrawl-delay: 0\n")
        if path == "/sitemap.xml":
            body = "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>" + "".join(
                f"<url><loc>{u}</loc></url>" for u in urls
            ) + "</urlset>"
            return httpx.Response(200, text=body)
        return httpx.Response(200, text=PROGRAM_HTML)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
    return SitemapHarvester(client=client)


class TestOrchestrator:
    async def test_full_flow_writes_and_reports(self) -> None:
        harvester = make_harvester(["https://test.edu/msc", "https://test.edu/admissions"])
        static = StaticEngine(client=harvester._client)
        router = AdaptiveRouter(static=static, stats=MemoryDomainStats())
        extractor = FakeExtractor([good_bundle(), good_bundle("MSc Admissions Info")])
        store = MemoryStore()
        progress = MemoryJobProgress(["EE"], "L1")

        orch = ResearchOrchestrator(
            router=router, harvester=harvester, inventory=FakeInventory([inst()]),
            extractor=extractor, store=store, progress_cb=progress.update,
        )
        summary = await orch.run(["EE"], depth=get_profile("L1"), write=True)

        assert summary.universities == 1
        assert summary.pages_fetched == 2
        assert summary.pages_extracted == 2
        assert summary.programs_written == 2
        assert ("inventory", 1, 1) in progress.updates
        assert ("universities", 1, 1) in progress.updates

    async def test_second_run_updates_without_duplicating(self) -> None:
        harvester = make_harvester(["https://test.edu/msc"])
        static = StaticEngine(client=harvester._client)
        router = AdaptiveRouter(static=static, stats=MemoryDomainStats())
        store = MemoryStore()

        def make_extractor():
            return FakeExtractor([good_bundle()])

        orch1 = ResearchOrchestrator(
            router=router, harvester=harvester, inventory=FakeInventory([inst()]),
            extractor=make_extractor(), store=store,
        )
        summary1 = await orch1.run(["EE"], depth=get_profile("L1"), write=True)
        assert summary1.programs_written == 1

        orch2 = ResearchOrchestrator(
            router=router, harvester=make_harvester(["https://test.edu/msc"]),
            inventory=FakeInventory([inst()]), extractor=make_extractor(), store=store,
        )
        summary2 = await orch2.run(["EE"], depth=get_profile("L1"), write=True)
        assert summary2.programs_updated == 1
        assert summary2.programs_written == 0
        assert len(store.programs) == 1

    async def test_dry_run_skips_writes(self) -> None:
        harvester = make_harvester(["https://test.edu/msc"])
        static = StaticEngine(client=harvester._client)
        router = AdaptiveRouter(static=static, stats=MemoryDomainStats())
        store = MemoryStore()
        orch = ResearchOrchestrator(
            router=router, harvester=harvester, inventory=FakeInventory([inst()]),
            extractor=FakeExtractor([good_bundle()]), store=store,
        )
        summary = await orch.run(["EE"], depth=get_profile("L1"), write=False)
        assert summary.pages_extracted == 1
        assert store.upserts == 0

    async def test_university_without_domain_skipped(self) -> None:
        harvester = make_harvester([])
        static = StaticEngine(client=harvester._client)
        router = AdaptiveRouter(static=static, stats=MemoryDomainStats())
        store = MemoryStore()
        orch = ResearchOrchestrator(
            router=router, harvester=harvester, inventory=FakeInventory([inst(domain=None)]),
            extractor=FakeExtractor([]), store=store,
        )
        summary = await orch.run(["EE"], depth=get_profile("L1"), write=True)
        assert summary.notes and "no domain" in summary.notes[0]


class TestQC:
    def test_non_cse_program_warns_but_passes(self) -> None:
        bundle = ExtractionBundle(
            program=ProgramExtraction(
                source_url="https://test.edu/msc",
                program_name=cited("MSc Medieval History", "MSc Medieval History"),
                field_tags=["history"],
            )
        )
        report = check_program(bundle, inst())
        assert report.passed is True
        assert any("not obviously CSE-relevant" in w for w in report.warnings)

    def test_stale_deadline_warns(self) -> None:
        bundle = ExtractionBundle(
            program=ProgramExtraction(
                source_url="https://test.edu/msc",
                program_name=cited("MSc Computer Science", "MSc Computer Science"),
                application_deadline=cited("2020-03-15", "Application deadline: 2020-03-15"),
                field_tags=["cs"],
            )
        )
        report = check_program(bundle, inst())
        assert any("stale" in w for w in report.warnings)
        assert report.passed is True

    def test_missing_name_fails(self) -> None:
        bundle = ExtractionBundle(program=ProgramExtraction(source_url="https://test.edu/msc"))
        report = check_program(bundle, inst())
        assert report.passed is False
        assert report.errors

    def test_zero_tuition_without_note_warns(self) -> None:
        bundle = ExtractionBundle(
            program=ProgramExtraction(
                source_url="https://test.edu/msc",
                program_name=cited("MSc Computer Science", "MSc Computer Science"),
                tuition_eur_per_year=cited({"amount_eur": 0.0, "note": ""}, "EUR 0"),
                field_tags=["cs"],
            )
        )
        report = check_program(bundle, inst())
        assert any("zero" in w for w in report.warnings)
