"""Adaptive fetch router (task 7).

Routing algorithm:
  1. Consult domain stats: if a best engine is remembered for the domain, use it.
  2. Otherwise probe STATIC first (cheapest).
  3. On FetchError or JS-shell/empty result, escalate PLAYWRIGHT, then CRAWL4AI.
  4. Record success (best engine) / failures per domain.

Acceptance: a JS-heavy domain escalates STATIC -> PLAYWRIGHT; remembered next time.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from europagrad_agent.engines.base import FetchEngine, FetchError, FetchResult
from europagrad_agent.engines.quality import assess
from europagrad_agent.storage.domain_stats import DomainStats, MemoryDomainStats

ENGINE_ORDER = ("STATIC", "JINA", "PLAYWRIGHT", "CRAWL4AI")


class AdaptiveRouter:
    def __init__(
        self,
        static: FetchEngine,
        playwright: FetchEngine | None = None,
        crawl4ai: FetchEngine | None = None,
        jina: FetchEngine | None = None,
        stats: DomainStats | None = None,
        use_memory_stats_fallback: bool = True,
    ) -> None:
        self._engines: dict[str, FetchEngine] = {static.name: static}
        if playwright is not None:
            self._engines[playwright.name] = playwright
        if crawl4ai is not None:
            self._engines[crawl4ai.name] = crawl4ai
        if jina is not None:
            self._engines[jina.name] = jina
        self._stats = stats or (MemoryDomainStats() if use_memory_stats_fallback else None)

    async def fetch(self, url: str) -> FetchResult:
        domain = urlsplit(url).netloc
        order = list(ENGINE_ORDER)

        remembered = await self._stats.get_best(domain) if self._stats else None
        if remembered in self._engines:
            order = [remembered] + [e for e in ENGINE_ORDER if e != remembered]

        last_error: Exception | None = None
        for name in order:
            engine = self._engines.get(name)
            if engine is None:
                continue
            try:
                result = await engine.fetch(url)
            except FetchError as err:
                last_error = err
                if self._stats:
                    await self._stats.record_failure(domain, name)
                continue

            if not self._usable(result):
                if self._stats:
                    await self._stats.record_failure(domain, name)
                last_error = FetchError(url, name, "content unusable (JS shell / empty)")
                continue

            if self._stats:
                await self._stats.record_success(domain, name)
            return result

        assert last_error is not None
        raise last_error

    @staticmethod
    def _usable(result: FetchResult) -> bool:
        if not result.ok:
            return False
        _chars, _density, shell = assess(result.html)
        return not shell
