"""Research orchestrator (task 11): spec §38 flow end-to-end.

  inventory → sitemap harvest → fetch (adaptive router) → extract (cited) →
  QC gate → idempotent upsert (+change_log)

Progress callback drives research_jobs.progress rows (storage.job_progress).
Dry-run mode executes every phase but skips DB writes.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Protocol

from europagrad_agent.engines.router import AdaptiveRouter
from europagrad_agent.extraction.schemas import ExtractionBundle
from europagrad_agent.registries.depth import DepthProfile
from europagrad_agent.registries.ror import Institution
from europagrad_agent.registries.sitemap import SitemapHarvester

ProgressCb = Callable[[str, int, int], Awaitable[None]]

CANDIDATE_LIMIT_DEFAULT = 8


class InventoryLoader(Protocol):
    async def load_country(self, iso2: str) -> list[Institution]: ...


class Extractor(Protocol):
    async def extract(self, url: str, page_text: str, target: str = "program") -> tuple[ExtractionBundle, list[str]]: ...


class ProgramStore(Protocol):
    async def upsert_program(self, university_id: str, bundle: ExtractionBundle) -> dict: ...

    async def get_university_id(self, institution: Institution) -> str | None: ...

    async def ensure_university(self, institution: Institution) -> str: ...


@dataclass
class RunSummary:
    countries: list[str]
    universities: int = 0
    pages_fetched: int = 0
    pages_extracted: int = 0
    programs_written: int = 0
    programs_updated: int = 0
    qc_warnings: int = 0
    qc_errors: int = 0
    notes: list[str] = field(default_factory=list)


class ResearchOrchestrator:
    def __init__(
        self,
        router: AdaptiveRouter,
        harvester: SitemapHarvester,
        inventory: InventoryLoader,
        extractor: Extractor,
        store: ProgramStore,
        progress_cb: ProgressCb | None = None,
    ) -> None:
        self._router = router
        self._harvester = harvester
        self._inventory = inventory
        self._extractor = extractor
        self._store = store
        self._progress = progress_cb

    async def _report(self, phase: str, done: int, total: int) -> None:
        if self._progress:
            await self._progress(phase, done, total)

    async def run(
        self,
        countries: list[str],
        depth: DepthProfile,
        write: bool = True,
        university_limit: int | None = None,
        candidate_limit: int = CANDIDATE_LIMIT_DEFAULT,
    ) -> RunSummary:
        summary = RunSummary(countries=list(countries))

        # Phase 1: inventory
        institutions: list[Institution] = []
        for cc in countries:
            institutions.extend(await self._inventory.load_country(cc))
        if university_limit is not None:
            with_domain = [i for i in institutions if i.domain]
            institutions = with_domain[:university_limit]
        summary.universities = len(institutions)
        await self._report("inventory", len(institutions), len(institutions))

        # Phase 2+3: harvest candidates, fetch, extract per university
        done = 0
        for institution in institutions:
            if not institution.domain:
                summary.notes.append(f"skip (no domain): {institution.name}")
                done += 1
                continue

            harvest = await self._harvester.harvest(institution.domain, cap=min(depth.domain_page_cap, candidate_limit))
            if not harvest.sitemap_found:
                summary.notes.append(f"no sitemap: {institution.domain}")
                done += 1
                continue

            university_id = await self._store.ensure_university(institution) if write else "dry-run"
            fetched = 0
            extracted = 0
            for url in harvest.candidates[: min(depth.domain_page_cap, candidate_limit)]:
                try:
                    result = await self._router.fetch(url)
                except Exception:
                    continue
                fetched += 1
                if not result.ok:
                    continue
                try:
                    bundle, _rejected = await self._extractor.extract(result.url, result.html)
                except Exception:
                    continue
                if bundle.program.program_name is None:
                    continue
                extracted += 1

                from europagrad_agent.pipelines.qc import check_program

                report = check_program(bundle, institution)
                summary.qc_warnings += len(report.warnings)
                if not report.passed:
                    summary.qc_errors += len(report.errors)
                    continue
                if write:
                    outcome = await self._store.upsert_program(university_id, bundle)
                    if outcome["created"]:
                        summary.programs_written += 1
                    else:
                        summary.programs_updated += 1

            summary.pages_fetched += fetched
            summary.pages_extracted += extracted
            done += 1
            await self._report("universities", done, len(institutions))

        return summary


async def gather_with_limit(coros: list[Awaitable], limit: int) -> list:
    sem = asyncio.Semaphore(limit)

    async def wrap(c: Awaitable):
        async with sem:
            return await c

    return await asyncio.gather(*(wrap(c) for c in coros))
