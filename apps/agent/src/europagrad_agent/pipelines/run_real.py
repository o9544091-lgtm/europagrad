"""Real research-run entrypoint (task 12): wires the orchestrator to live storage.

Used by the CLI and the GitHub Actions runner. Extractor selection:
  auto    → LLM path when OPENROUTER_API_KEY is set, else heuristic
  llm     → force LLM (raises without key)
  heuristic → keyless citation-validated extraction
"""

from __future__ import annotations

from dataclasses import asdict

from europagrad_agent.config import get_settings
from europagrad_agent.engines.router import AdaptiveRouter
from europagrad_agent.engines.static import StaticEngine
from europagrad_agent.pipelines.heuristic import HeuristicExtractor
from europagrad_agent.pipelines.orchestrator import ResearchOrchestrator
from europagrad_agent.registries.depth import get_profile
from europagrad_agent.registries.ror_dump import RorDumpLoader
from europagrad_agent.registries.sitemap import SitemapHarvester
from europagrad_agent.storage.domain_stats import MemoryDomainStats, SupabaseDomainStats
from europagrad_agent.storage.job_progress import JobProgress, MemoryJobProgress
from europagrad_agent.storage.universities import UniversityStore
from europagrad_agent.storage.writer import ProgramWriter


def _optional_tiers() -> tuple[object | None, object | None, object | None]:
    playwright = None
    crawl4ai_engine = None
    jina = None
    try:
        import playwright.async_api  # noqa: F401

        from europagrad_agent.engines.playwright_engine import PlaywrightEngine

        playwright = PlaywrightEngine()
    except (ImportError, RuntimeError):
        pass
    try:
        import crawl4ai  # noqa: F401

        from europagrad_agent.engines.crawl4ai_engine import Crawl4AIEngine

        crawl4ai_engine = Crawl4AIEngine()
    except (ImportError, RuntimeError):
        pass
    try:
        from europagrad_agent.engines.jina_reader import JinaReaderEngine

        jina = JinaReaderEngine()
    except (ImportError, RuntimeError):
        pass
    return playwright, crawl4ai_engine, jina


def _build_extractor(kind: str):
    settings = get_settings()
    if kind == "heuristic":
        return HeuristicExtractor()
    if kind == "llm":
        from europagrad_agent.extraction.service import ExtractionService

        return ExtractionService()
    # auto
    if settings.openrouter_api_key:
        from europagrad_agent.extraction.service import ExtractionService

        return ExtractionService()
    return HeuristicExtractor()


class _CombinedStore:
    def __init__(self) -> None:
        self._universities = UniversityStore()
        self._writer = ProgramWriter()

    async def ensure_university(self, institution):
        return await self._universities.ensure_university(institution)

    async def get_university_id(self, institution):
        return await self._universities.get_university_id(institution)

    async def upsert_program(self, university_id: str, bundle):
        return await self._writer.upsert_program(university_id, bundle)


async def execute_real_run(
    countries: list[str],
    depth_level: str,
    extractor_kind: str = "auto",
    university_limit: int | None = None,
    candidate_limit: int = 8,
    job_id: str | None = None,
) -> dict:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError("Real runs require SUPABASE_URL + SUPABASE_SERVICE_KEY")

    profile = get_profile(depth_level)
    try:
        stats = SupabaseDomainStats()
    except RuntimeError:
        stats = MemoryDomainStats()

    static = StaticEngine()
    playwright, crawl4ai, jina = _optional_tiers()
    router = AdaptiveRouter(
        static=static, playwright=playwright, crawl4ai=crawl4ai, jina=jina, stats=stats
    )
    harvester = SitemapHarvester()
    inventory = RorDumpLoader()
    extractor = _build_extractor(extractor_kind)
    store = _CombinedStore()

    try:
        job = JobProgress(countries, depth_level, job_id=job_id)
    except RuntimeError:
        job = MemoryJobProgress(countries, depth_level)

    orch = ResearchOrchestrator(
        router=router,
        harvester=harvester,
        inventory=inventory,
        extractor=extractor,
        store=store,
        progress_cb=job.update,
    )
    try:
        summary = await orch.run(
            countries,
            depth=profile,
            write=True,
            university_limit=university_limit,
            candidate_limit=candidate_limit,
        )
        job.finish("DONE", summary=asdict(summary))
        return asdict(summary)
    except Exception as err:
        job.finish("FAILED", error=str(err))
        raise
