"""Search provider abstraction + Tavily implementation (task 9).

SearchProvider returns organic results paginated to a depth cap. Tavily free
tier: 1000 credits/month; each request = 1 credit regardless of depth param,
so depth is implemented as N sequential requests (max_results per request).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

import httpx

TAVILY_ENDPOINT = "https://api.tavily.com/search"


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    snippet: str = ""
    score: float = 0.0


@dataclass
class SearchPage:
    page: int
    results: list[SearchResult] = field(default_factory=list)


class SearchProvider(Protocol):
    name: str

    async def search(
        self,
        query: str,
        page: int = 1,
        max_results: int = 10,
        include_domains: list[str] | None = None,
    ) -> list[SearchResult]: ...


class SearchError(Exception):
    pass


class TavilyProvider:
    name = "TAVILY"

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        if not api_key:
            raise ValueError("TavilyProvider requires an API key")
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def search(
        self,
        query: str,
        page: int = 1,
        max_results: int = 10,
        include_domains: list[str] | None = None,
    ) -> list[SearchResult]:
        payload: dict = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max(1, min(max_results * max(page, 1), 20)),
            "search_depth": "basic",
        }
        if include_domains:
            payload["include_domains"] = include_domains
        try:
            resp = await self._client.post(TAVILY_ENDPOINT, json=payload)
        except httpx.HTTPError as err:
            raise SearchError(f"tavily request failed: {err}") from err
        if resp.status_code == 429:
            raise SearchError("tavily rate limit exceeded")
        if resp.status_code >= 400:
            raise SearchError(f"tavily error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        raw = data.get("results", [])
        window = raw[(page - 1) * max_results : page * max_results]
        return [
            SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                snippet=item.get("content", "")[:400],
                score=float(item.get("score", 0.0)),
            )
            for item in window
            if item.get("url")
        ]


class QueryExpansion:
    """Spec §23 query templates, parameterized per country and intent."""

    INTENTS: dict[str, tuple[str, ...]] = {
        "programmes": (
            "Computer Science MSc {country}",
            "Artificial Intelligence MSc {country}",
            "Data Science MSc {country}",
            "English taught master's computer science {country}",
        ),
        "scholarships": (
            "government scholarship {country} international students masters",
            "fully funded scholarship {country} computer science masters",
        ),
        "language": (
            "MOI IELTS waiver master's {country}",
            "English test requirement waiver {country} university",
        ),
        "work": (
            "international students part time work rules {country}",
            "student visa work rights {country} hours",
        ),
        "joint": (
            "Erasmus Mundus joint master's computer science",
        ),
    }

    def expand(
        self,
        country: str,
        intents: tuple[Literal["programmes", "scholarships", "language", "work", "joint"], ...] = (
            "programmes",
            "scholarships",
            "language",
            "work",
        ),
    ) -> list[str]:
        queries: list[str] = []
        for intent in intents:
            for template in self.INTENTS[intent]:
                queries.append(template.format(country=country))
        return queries
