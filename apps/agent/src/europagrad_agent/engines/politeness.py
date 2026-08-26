"""Politeness layer: robots.txt cache + per-domain throttle (task 6).

Rules honored per AGENTS.md golden rule 7: robots.txt respected, per-domain
rate limits, realistic UA, concurrency caps.
"""

from __future__ import annotations

import asyncio
import time
from io import StringIO
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "EuropaGradResearchBot/0.1 (+https://europagrad.example; research; contact: ops@europagrad.example)"
ROBOTS_TIMEOUT_S = 10.0
ROBOTS_TTL_S = 3600.0


class RobotCache:
    """Caches robots.txt per domain; treats fetch failure as allow (industry default),
    4xx-with-body as disallow-all per RFC 9309, and HTML-instead-of-robots as absent."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=ROBOTS_TIMEOUT_S
        )
        self._cache: dict[str, tuple[float, RobotFileParser | None]] = {}
        self._sitemaps: dict[str, tuple[float, list[str]]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    @staticmethod
    def _looks_like_html(body: str) -> bool:
        head = body.lstrip()[:200].lower()
        return head.startswith("<!doctype") or head.startswith("<html") or "<meta" in head[:100]

    async def _fetch_robots(self, origin: str) -> RobotFileParser | None:
        robots_url = f"{origin}/robots.txt"
        try:
            resp = await self._client.get(robots_url)
        except httpx.HTTPError:
            return None
        parser = RobotFileParser()
        if resp.status_code >= 500:
            return None
        if resp.status_code in (401, 403):
            parser.parse(["User-agent: *", "Disallow: /"])
            return parser
        if self._looks_like_html(resp.text):
            return None
        parser.parse(StringIO(resp.text).readlines())
        return parser

    async def _robots_for(self, origin: str) -> RobotFileParser | None:
        now = time.monotonic()
        async with self._locks.setdefault(origin, asyncio.Lock()):
            hit = self._cache.get(origin)
            if hit is None or now - hit[0] > ROBOTS_TTL_S:
                parser = await self._fetch_robots(origin)
                self._cache[origin] = (now, parser)
            else:
                parser = hit[1]
        return parser

    async def allowed(self, url: str) -> bool:
        parser = await self._robots_for(f"{urlsplit(url).scheme}://{urlsplit(url).netloc}")
        if parser is None:
            return True
        return parser.can_fetch(USER_AGENT, url)

    async def crawl_delay(self, url: str) -> float:
        parser = await self._robots_for(f"{urlsplit(url).scheme}://{urlsplit(url).netloc}")
        if parser is None:
            return 0.0
        delay = parser.crawl_delay(USER_AGENT)
        return float(delay) if delay else 0.0

    async def declared_sitemaps(self, url: str) -> list[str]:
        """Sitemap: URLs declared inside robots.txt (standard discovery mechanism)."""
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        now = time.monotonic()
        async with self._locks.setdefault(f"sm:{origin}", asyncio.Lock()):
            hit = self._sitemaps.get(origin)
            if hit is None or now - hit[0] > ROBOTS_TTL_S:
                parser = await self._robots_for(origin)
                sitemaps: list[str] = []
                if parser is not None:
                    sitemaps = [
                        entry if "://" in entry else f"{origin}{entry}"
                        for entry in parser.site_maps() or []
                    ]
                self._sitemaps[origin] = (now, sitemaps)
        return self._sitemaps[origin][1]


class DomainThrottle:
    """Enforces min interval per domain; asyncio-safe."""

    def __init__(self, min_interval_s: float = 1.0, robots_delay_factor: float = 1.5) -> None:
        self.min_interval_s = min_interval_s
        self.robots_delay_factor = robots_delay_factor
        self._last: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def wait(self, domain: str, robots_delay_s: float = 0.0) -> None:
        interval = max(self.min_interval_s, robots_delay_s * self.robots_delay_factor)
        lock = self._locks.setdefault(domain, asyncio.Lock())
        async with lock:
            now = time.monotonic()
            last = self._last.get(domain)
            if last is not None:
                elapsed = now - last
                if elapsed < interval:
                    await asyncio.sleep(interval - elapsed)
            self._last[domain] = time.monotonic()
