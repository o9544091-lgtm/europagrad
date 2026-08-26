"""Crawl4AI optional tier (task 7): last resort for stubborn domains.

Runs via `crawl4ai` Python package when installed (uv sync --extra crawl4ai).
Its markdown output is particularly well-suited for LLM extraction.
"""

from __future__ import annotations

import time

from europagrad_agent.engines.base import FetchError, FetchResult


def _import_crawl4ai():
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError as err:
        raise RuntimeError(
            "Crawl4AI tier not installed. Run: uv sync --extra crawl4ai"
        ) from err
    return AsyncWebCrawler


class Crawl4AIEngine:
    name = "CRAWL4AI"

    async def fetch(self, url: str) -> FetchResult:
        AsyncWebCrawler = _import_crawl4ai()
        started = time.monotonic()
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url, cache_mode="bypass")
        except RuntimeError as err:
            raise FetchError(url, self.name, str(err)) from err
        except Exception as err:
            raise FetchError(url, self.name, f"crawl error: {err}") from err

        fetch_ms = int((time.monotonic() - started) * 1000)
        if not result.success:
            raise FetchError(url, self.name, result.error_message or "unsuccessful")

        html = result.html or ""
        text = result.markdown or ""
        return FetchResult(
            url=result.url or url,
            status=200,
            engine=self.name,
            html=html,
            text_chars=len(text),
            links=list(result.links.get("internal", {}).keys())
            + list(result.links.get("external", {}).keys())
            if isinstance(result.links, dict)
            else [],
            fetch_ms=fetch_ms,
        )
