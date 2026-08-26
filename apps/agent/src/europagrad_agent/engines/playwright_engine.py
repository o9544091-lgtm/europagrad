"""Playwright-Python escalation tier (task 7).

Used only for domains where the static probe failed (JS shell / block status).
Browsers are installed via `uv sync --extra browser && uv run playwright install chromium`.
ImportGuard: importing this module fails gracefully when playwright is absent.
"""

from __future__ import annotations

import time

from europagrad_agent.engines.base import FetchError, FetchResult
from europagrad_agent.engines.quality import assess, extract_links


def _import_playwright():
    try:
        from playwright.async_api import async_playwright
    except ImportError as err:
        raise RuntimeError(
            "Playwright tier not installed. Run: uv sync --extra browser; "
            "uv run playwright install chromium"
        ) from err
    return async_playwright


class PlaywrightEngine:
    name = "PLAYWRIGHT"

    def __init__(self, nav_timeout_ms: int = 30000, total_timeout_ms: int = 60000) -> None:
        self._nav_timeout_ms = nav_timeout_ms
        self._total_timeout_ms = total_timeout_ms

    async def fetch(self, url: str) -> FetchResult:
        started = time.monotonic()
        try:
            async_playwright = _import_playwright()
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                try:
                    context = await browser.new_context(
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 "
                            "EuropaGradResearchBot/0.1"
                        ),
                        locale="en-US",
                    )
                    page = await context.new_page()
                    resp = await page.goto(url, wait_until="networkidle", timeout=self._nav_timeout_ms)
                    status = resp.status if resp else 0
                    html = await page.content()
                    final_url = page.url
                finally:
                    await browser.close()
        except RuntimeError as err:
            raise FetchError(url, self.name, str(err)) from err
        except Exception as err:
            raise FetchError(url, self.name, f"browser error: {err}") from err

        fetch_ms = int((time.monotonic() - started) * 1000)
        if status in (403, 429) or status >= 500:
            raise FetchError(url, self.name, f"status {status}")

        text_chars, _density, _shell = assess(html)
        return FetchResult(
            url=final_url,
            status=status or 200,
            engine=self.name,
            html=html,
            text_chars=text_chars,
            links=extract_links(html, final_url),
            fetch_ms=fetch_ms,
        )
