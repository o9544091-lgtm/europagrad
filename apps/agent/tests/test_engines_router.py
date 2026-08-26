"""Task 7 tests: escalation chain, adaptive routing with memory, JS-shell usability."""

from __future__ import annotations

import httpx
import pytest

from engine_helpers import ScriptedEngine, ok, shell
from europagrad_agent.engines.base import FetchError
from europagrad_agent.engines.router import AdaptiveRouter
from europagrad_agent.engines.static import StaticEngine
from europagrad_agent.storage.domain_stats import MemoryDomainStats
from html_fixtures import JS_SHELL_HTML


def make_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)


class TestEscalation:
    async def test_js_shell_escalates_to_playwright(self) -> None:
        static = ScriptedEngine("STATIC", [shell("STATIC")])
        pw = ScriptedEngine("PLAYWRIGHT", [ok("PLAYWRIGHT")])
        router = AdaptiveRouter(static=static, playwright=pw, stats=MemoryDomainStats())
        result = await router.fetch("https://x.edu/p")
        assert result.engine == "PLAYWRIGHT"
        assert len(static.calls) == 1 and len(pw.calls) == 1

    async def test_error_escalates_then_success(self) -> None:
        static = ScriptedEngine("STATIC", [FetchError("https://x.edu/p", "STATIC", "status 403")])
        pw = ScriptedEngine("PLAYWRIGHT", [ok("PLAYWRIGHT")])
        router = AdaptiveRouter(static=static, playwright=pw, stats=MemoryDomainStats())
        result = await router.fetch("https://x.edu/p")
        assert result.engine == "PLAYWRIGHT"

    async def test_all_fail_raises_last(self) -> None:
        static = ScriptedEngine("STATIC", [FetchError("https://x.edu/p", "STATIC", "status 429")])
        pw = ScriptedEngine("PLAYWRIGHT", [FetchError("https://x.edu/p", "PLAYWRIGHT", "timeout")])
        router = AdaptiveRouter(static=static, playwright=pw, stats=MemoryDomainStats())
        with pytest.raises(FetchError, match="timeout"):
            await router.fetch("https://x.edu/p")

    async def test_static_success_skips_escalation(self) -> None:
        static = ScriptedEngine("STATIC", [ok("STATIC")])
        pw = ScriptedEngine("PLAYWRIGHT", [])
        router = AdaptiveRouter(static=static, playwright=pw, stats=MemoryDomainStats())
        result = await router.fetch("https://x.edu/p")
        assert result.engine == "STATIC"
        assert pw.calls == []


class TestDomainMemory:
    async def test_remembered_engine_used_first(self) -> None:
        stats = MemoryDomainStats()
        await stats.record_success("x.edu", "PLAYWRIGHT")

        static = ScriptedEngine("STATIC", [])
        pw = ScriptedEngine("PLAYWRIGHT", [ok("PLAYWRIGHT")])
        router = AdaptiveRouter(static=static, playwright=pw, stats=stats)

        result = await router.fetch("https://x.edu/p")
        assert result.engine == "PLAYWRIGHT"
        assert static.calls == []

    async def test_success_updates_memory(self) -> None:
        stats = MemoryDomainStats()
        static = ScriptedEngine("STATIC", [shell("STATIC")])
        pw = ScriptedEngine("PLAYWRIGHT", [ok("PLAYWRIGHT")])
        router = AdaptiveRouter(static=static, playwright=pw, stats=stats)

        await router.fetch("https://x.edu/p")
        assert await stats.get_best("x.edu") == "PLAYWRIGHT"

    async def test_missing_optional_engines_are_skipped(self) -> None:
        static = ScriptedEngine("STATIC", [FetchError("https://x.edu/p", "STATIC", "status 403")])
        router = AdaptiveRouter(static=static, playwright=None, crawl4ai=None, stats=MemoryDomainStats())
        with pytest.raises(FetchError):
            await router.fetch("https://x.edu/p")


class TestPlaywrightEngineImportGuard:
    async def test_missing_playwright_raises_fetch_error(self) -> None:
        from europagrad_agent.engines.playwright_engine import PlaywrightEngine

        try:
            import playwright  # noqa: F401
        except ImportError:
            pass
        else:
            pytest.skip("playwright installed; guard path not testable here")

        engine = PlaywrightEngine()
        with pytest.raises(FetchError, match="not installed"):
            await engine.fetch("https://x.edu/p")


class TestIntegrationStaticRouter:
    async def test_static_js_shell_routes_up(self) -> None:
        """Integration: real StaticEngine over mock transport serving a JS shell."""

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nAllow: /\n")
            return httpx.Response(200, text=JS_SHELL_HTML)

        static = StaticEngine(client=make_client(handler))
        pw = ScriptedEngine("PLAYWRIGHT", [ok("PLAYWRIGHT")])
        router = AdaptiveRouter(static=static, playwright=pw, stats=MemoryDomainStats())
        result = await router.fetch("https://shell.edu/app")
        assert result.engine == "PLAYWRIGHT"
