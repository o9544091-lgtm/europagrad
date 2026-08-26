"""Jina Reader fetch tier (r.jina.ai) — optional, key-boosted (task 12+).

Returns clean markdown for JS-heavy pages without a local browser. Works
keyless at low rates; a free Jina key raises limits. Sits between STATIC and
PLAYWRIGHT in the escalation chain.
"""

from __future__ import annotations

import time

import httpx

from europagrad_agent.config import get_settings
from europagrad_agent.engines.base import FetchError, FetchResult
from europagrad_agent.engines.quality import assess

JINA_READER_BASE = "https://r.jina.ai"


class JinaReaderEngine:
    name = "JINA"

    def __init__(self, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self._api_key = api_key if api_key is not None else get_settings().jina_api_key
        self._client = client or httpx.AsyncClient(
            headers={"Accept": "text/plain"},
            follow_redirects=True,
            timeout=60.0,
        )

    async def fetch(self, url: str) -> FetchResult:
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        started = time.monotonic()
        try:
            resp = await self._client.get(f"{JINA_READER_BASE}/{url}", headers=headers)
        except httpx.HTTPError as err:
            raise FetchError(url, self.name, f"reader error: {err}") from err
        fetch_ms = int((time.monotonic() - started) * 1000)

        if resp.status_code == 429:
            raise FetchError(url, self.name, "reader rate limited")
        if resp.status_code >= 400:
            raise FetchError(url, self.name, f"status {resp.status_code}")

        markdown = resp.text
        text_chars, _density, _shell = assess(markdown)
        return FetchResult(
            url=url,
            status=resp.status_code,
            engine=self.name,
            html=markdown,
            text_chars=text_chars,
            links=[],
            fetch_ms=fetch_ms,
        )
