"""Keyless DuckDuckGo search provider (task 12).

Zero-key fallback so research runs work before a Tavily key is configured.
Uses the HTML endpoints politely (low volume, per-run caps). Quality/caps are
below Tavily — set TAVILY_API_KEY to upgrade; the interface is identical.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

import httpx
from selectolax.parser import HTMLParser

from europagrad_agent.search.provider import SearchError, SearchResult

DDG_ENDPOINT = "https://html.duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class DuckDuckGoProvider:
    name = "DDG"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=20.0
        )

    async def search(
        self,
        query: str,
        page: int = 1,
        max_results: int = 10,
        include_domains: list[str] | None = None,
    ) -> list[SearchResult]:
        if page > 5:
            return []
        try:
            resp = await self._client.post(
                DDG_ENDPOINT,
                data={"q": query, "s": str((page - 1) * 30), "kl": "wt-wt"},
            )
        except httpx.HTTPError as err:
            raise SearchError(f"ddg request failed: {err}") from err
        if resp.status_code == 403 or "anomaly" in resp.text.lower()[:500]:
            raise SearchError("ddg rate limited (403/anomaly detection)")
        if resp.status_code >= 400:
            raise SearchError(f"ddg error {resp.status_code}")

        results: list[SearchResult] = []
        try:
            tree = HTMLParser(resp.text)
        except Exception:
            return results
        for node in tree.css("div.result") or tree.css("div.web-result"):
            link = node.css_first("a.result__a")
            if link is None:
                continue
            url = self._clean_url(link.attributes.get("href", ""))
            if not url:
                continue
            if include_domains and not any(d in url for d in include_domains):
                continue
            snippet_node = node.css_first(".result__snippet")
            title = link.text(strip=True)
            results.append(
                SearchResult(
                    url=url,
                    title=title,
                    snippet=snippet_node.text(strip=True)[:400] if snippet_node else "",
                    score=1.0 / (len(results) + 1),
                )
            )
            if len(results) >= max_results:
                break
        return results

    @staticmethod
    def _clean_url(href: str) -> str:
        if not href:
            return ""
        if href.startswith("//duckduckgo.com/l/") or "duckduckgo.com/l/" in href:
            parsed = urlsplit(href if "://" in href else f"https:{href}")
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            return target
        if href.startswith("//"):
            return f"https:{href}"
        return href if href.startswith("http") else ""
