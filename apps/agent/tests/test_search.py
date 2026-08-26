"""Task 9 tests: Tavily provider (mocked HTTP) + query expansion."""

from __future__ import annotations

import httpx
import pytest

from europagrad_agent.search.provider import (
    QueryExpansion,
    SearchError,
    TavilyProvider,
)


def tavily_response(urls: list[str]) -> dict:
    return {
        "results": [
            {"url": u, "title": f"Title {u}", "content": f"Snippet {u}", "score": 0.9}
            for u in urls
        ]
    }


def make_provider(responses: list[dict | Exception]) -> tuple[TavilyProvider, list[dict]]:
    sent: list[dict] = []
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        import json as jsonlib

        sent.append(jsonlib.loads(request.content))
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return httpx.Response(200, json=item)

    provider = TavilyProvider(api_key="test-key", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    return provider, sent


class TestTavilyProvider:
    async def test_basic_search_maps_results(self) -> None:
        provider, sent = make_provider([tavily_response(["https://a.edu", "https://b.gov"])])
        results = await provider.search("cs msc italy", page=1, max_results=2)
        assert [r.url for r in results] == ["https://a.edu", "https://b.gov"]
        assert sent[0]["query"] == "cs msc italy"
        assert sent[0]["max_results"] == 2

    async def test_page2_refetches_deeper_and_windows(self) -> None:
        provider, sent = make_provider(
            [tavily_response([f"https://u{i}.edu" for i in range(1, 21)])]
        )
        results = await provider.search("q", page=2, max_results=10)
        assert [r.url for r in results] == [f"https://u{i}.edu" for i in range(11, 21)]
        assert sent[0]["max_results"] == 20

    async def test_rate_limit_raises_search_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": "rate"})

        provider = TavilyProvider(api_key="k", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        with pytest.raises(SearchError, match="rate limit"):
            await provider.search("q")

    async def test_include_domains_forwarded(self) -> None:
        provider, sent = make_provider([tavily_response(["https://daad.de/x"])])
        await provider.search("scholarship germany", include_domains=["daad.de"])
        assert sent[0]["include_domains"] == ["daad.de"]

    async def test_missing_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="API key"):
            TavilyProvider(api_key="")


class TestQueryExpansion:
    def test_default_intents_cover_spec_23(self) -> None:
        queries = QueryExpansion().expand("Italy")
        assert len(queries) == 10
        assert "Computer Science MSc Italy" in queries
        assert "government scholarship Italy international students masters" in queries
        assert "MOI IELTS waiver master's Italy" in queries
        assert "international students part time work rules Italy" in queries

    def test_intent_selection(self) -> None:
        queries = QueryExpansion().expand("Germany", intents=("joint",))
        assert queries == ["Erasmus Mundus joint master's computer science"]

    def test_no_unformatted_templates(self) -> None:
        for q in QueryExpansion().expand("France"):
            assert "{country}" not in q
