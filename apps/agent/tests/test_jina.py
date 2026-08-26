"""Tests for Jina integrations (reader fetch tier + search provider)."""

from __future__ import annotations

import httpx
import pytest

from engine_helpers import ScriptedEngine, ok
from europagrad_agent.engines.base import FetchError
from europagrad_agent.engines.jina_reader import JinaReaderEngine
from europagrad_agent.engines.quality import assess
from europagrad_agent.engines.router import AdaptiveRouter
from europagrad_agent.search.jina import JinaSearchProvider
from europagrad_agent.search.provider import SearchError
from europagrad_agent.storage.domain_stats import MemoryDomainStats

MARKDOWN = (
    "# MSc Computer Science\n\n"
    "The programme is taught entirely in English and takes 24 months to complete. "
    "Tuition for non-EU students is EUR 2,000 per year with several scholarships available. "
    "Applicants need IELTS 6.5 overall and a bachelor degree in computer science or related field."
)


class TestQualityMarkdown:
    def test_markdown_not_treated_as_shell(self) -> None:
        chars, density, shell = assess(MARKDOWN)
        assert chars > 200
        assert density == 1.0
        assert shell is False

    def test_empty_content_is_shell(self) -> None:
        assert assess("")[2] is True


class TestJinaReaderEngine:
    async def test_fetch_returns_markdown_result(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url).startswith("https://r.jina.ai/https://x.edu/msc")
            return httpx.Response(200, text=MARKDOWN)

        engine = JinaReaderEngine(api_key="test-key", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        result = await engine.fetch("https://x.edu/msc")
        assert result.engine == "JINA"
        assert result.text_chars > 200
        assert "MSc Computer Science" in result.html

    async def test_rate_limit_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, text="slow down")

        engine = JinaReaderEngine(api_key=None, client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        with pytest.raises(FetchError, match="rate"):
            await engine.fetch("https://x.edu/msc")

    async def test_router_uses_jina_after_static_failure(self) -> None:
        static = ScriptedEngine("STATIC", [FetchError("https://x.edu/p", "STATIC", "status 403")])
        jina = ScriptedEngine("JINA", [ok("JINA")])
        router = AdaptiveRouter(static=static, jina=jina, stats=MemoryDomainStats())
        result = await router.fetch("https://x.edu/p")
        assert result.engine == "JINA"


class TestJinaSearchProvider:
    async def test_parses_data_shape(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Authorization"] == "Bearer jk-test"
            return httpx.Response(200, json={
                "data": [
                    {"title": "DAAD", "url": "https://daad.de/x", "description": "scholarships"},
                    {"title": "No URL", "url": ""},
                ]
            })

        provider = JinaSearchProvider(api_key="jk-test", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        results = await provider.search("scholarship germany", max_results=5)
        assert [r.url for r in results] == ["https://daad.de/x"]

    async def test_parses_results_shape(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"results": [{"title": "T", "url": "https://a.edu"}]})

        provider = JinaSearchProvider(api_key="jk", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        results = await provider.search("q")
        assert results[0].url == "https://a.edu"

    async def test_credits_exhausted_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(402, text="payment required")

        provider = JinaSearchProvider(api_key="jk", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        with pytest.raises(SearchError, match="credits"):
            await provider.search("q")

    async def test_missing_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="API key"):
            JinaSearchProvider(api_key="")
