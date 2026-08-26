"""Task 6 tests: static engine, politeness, quality heuristics, domain stats."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import httpx
import pytest

from europagrad_agent.engines.base import FetchError
from europagrad_agent.engines.politeness import DomainThrottle
from europagrad_agent.engines.quality import assess, extract_links
from europagrad_agent.engines.static import StaticEngine
from europagrad_agent.storage.domain_stats import MemoryDomainStats

FIXTURES = Path(__file__).parent / "fixtures"
PROGRAM_HTML = (FIXTURES / "program_page.html").read_text(encoding="utf-8")
JS_SHELL_HTML = (FIXTURES / "js_shell.html").read_text(encoding="utf-8")


def make_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)


class TestQuality:
    def test_real_page_is_not_js_shell(self) -> None:
        chars, _density, shell = assess(PROGRAM_HTML)
        assert chars > 600
        assert shell is False

    def test_js_shell_detected(self) -> None:
        _chars, _density, shell = assess(JS_SHELL_HTML)
        assert shell is True

    def test_empty_is_shell(self) -> None:
        assert assess("")[2] is True

    def test_links_absolutized(self) -> None:
        links = extract_links(PROGRAM_HTML, "https://example-university.edu/en/programmes/msc-cs")
        assert "https://example-university.edu/en/education" in links
        assert "https://example-university.edu/en/scholarships" in links
        assert all(not link.startswith("#") for link in links)


class TestRobots:
    async def test_disallowed_url_raises(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nDisallow: /private/\nCrawl-delay: 0")
            if request.url.path.startswith("/private/"):
                return httpx.Response(200, text=PROGRAM_HTML)
            return httpx.Response(404)

        engine = StaticEngine(client=make_client(handler))
        with pytest.raises(FetchError, match="robots"):
            await engine.fetch("https://example-university.edu/private/programme")

    async def test_allowed_url_fetched(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nAllow: /\n")
            return httpx.Response(200, text=PROGRAM_HTML)

        engine = StaticEngine(client=make_client(handler))
        result = await engine.fetch("https://example-university.edu/en/msc-cs")
        assert result.ok is True
        assert result.engine == "STATIC"
        assert result.text_chars > 600


class TestErrorStatuses:
    @pytest.mark.parametrize("status", [403, 429, 500])
    async def test_block_statuses_raise(self, status: int) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nAllow: /\n")
            return httpx.Response(status)

        engine = StaticEngine(client=make_client(handler))
        with pytest.raises(FetchError):
            await engine.fetch("https://example-university.edu/en/msc-cs")


class TestThrottle:
    async def test_same_domain_throttled(self) -> None:
        throttle = DomainThrottle(min_interval_s=0.2)
        start = time.monotonic()
        await throttle.wait("a.edu")
        await throttle.wait("a.edu")
        assert time.monotonic() - start >= 0.19

    async def test_different_domains_independent(self) -> None:
        throttle = DomainThrottle(min_interval_s=0.5)
        start = time.monotonic()
        await asyncio.gather(throttle.wait("a.edu"), throttle.wait("b.edu"))
        assert time.monotonic() - start < 0.5


class TestDomainStats:
    async def test_memory_stats_flow(self) -> None:
        stats = MemoryDomainStats()
        assert await stats.get_best("a.edu") is None
        await stats.record_failure("a.edu", "STATIC")
        await stats.record_failure("a.edu", "STATIC")
        await stats.record_success("a.edu", "PLAYWRIGHT")
        assert await stats.get_best("a.edu") == "PLAYWRIGHT"
