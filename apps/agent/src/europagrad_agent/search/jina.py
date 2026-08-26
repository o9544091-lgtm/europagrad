"""Jina search provider (s.jina.ai) — optional third search backend (task 12+).

Activated when JINA_API_KEY is set. Free-tier trial credits make it a usable
secondary; Tavily (1000/mo replenishing) remains the preferred upgrade over
the keyless DDG default. Response parsing is tolerant across known shapes.
"""

from __future__ import annotations

from urllib.parse import quote

import httpx

from europagrad_agent.search.provider import SearchError, SearchResult

JINA_SEARCH_ENDPOINT = "https://s.jina.ai"


class JinaSearchProvider:
    name = "JINA"

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        if not api_key:
            raise ValueError("JinaSearchProvider requires an API key")
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def search(
        self,
        query: str,
        page: int = 1,
        max_results: int = 10,
        include_domains: list[str] | None = None,
    ) -> list[SearchResult]:
        if page > 1:
            return []
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            resp = await self._client.post(
                JINA_SEARCH_ENDPOINT,
                headers=headers,
                json={"q": query},
            )
        except httpx.HTTPError as err:
            raise SearchError(f"jina search failed: {err}") from err
        if resp.status_code == 402:
            raise SearchError("jina credits exhausted")
        if resp.status_code == 429:
            raise SearchError("jina rate limit exceeded")
        if resp.status_code >= 400:
            raise SearchError(f"jina error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        raw = data.get("data") or data.get("results") or []
        if isinstance(raw, dict):
            raw = [raw]

        results: list[SearchResult] = []
        for item in raw:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            if include_domains and not any(d in url for d in include_domains):
                continue
            results.append(
                SearchResult(
                    url=url,
                    title=(item.get("title") or "").strip(),
                    snippet=(item.get("description") or item.get("content") or "")[:400],
                    score=float(item.get("score") or 0.0) or (1.0 / (len(results) + 1)),
                )
            )
            if len(results) >= max_results:
                break
        return results

    @staticmethod
    def encoded_query(query: str) -> str:
        return quote(query, safe="")
