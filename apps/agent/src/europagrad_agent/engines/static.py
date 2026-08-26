"""Static HTTP fetch tier: httpx + lxml. The probe engine for every domain."""

from __future__ import annotations

import time

import httpx

from europagrad_agent.engines.base import FetchError, FetchResult
from europagrad_agent.engines.politeness import USER_AGENT, DomainThrottle, RobotCache
from europagrad_agent.engines.quality import assess, extract_links


class StaticEngine:
    name = "STATIC"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        robots: RobotCache | None = None,
        throttle: DomainThrottle | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en",
            },
            follow_redirects=True,
            timeout=20.0,
        )
        self._robots = robots or RobotCache(self._client)
        self._throttle = throttle or DomainThrottle()

    async def fetch(self, url: str) -> FetchResult:
        if not await self._robots.allowed(url):
            raise FetchError(url, self.name, "disallowed by robots.txt")

        from urllib.parse import urlsplit

        domain = urlsplit(url).netloc
        delay = await self._robots.crawl_delay(url)
        await self._throttle.wait(domain, delay)

        started = time.monotonic()
        try:
            resp = await self._client.get(url)
        except httpx.HTTPError as err:
            raise FetchError(url, self.name, f"http error: {err}") from err
        fetch_ms = int((time.monotonic() - started) * 1000)

        if resp.status_code in (403, 429) or resp.status_code >= 500:
            raise FetchError(url, self.name, f"status {resp.status_code}")

        raw = resp.text
        text_chars, _density, _shell = assess(raw)
        return FetchResult(
            url=str(resp.url),
            status=resp.status_code,
            engine=self.name,
            html=raw,
            text_chars=text_chars,
            links=extract_links(raw, str(resp.url)),
            fetch_ms=fetch_ms,
        )
