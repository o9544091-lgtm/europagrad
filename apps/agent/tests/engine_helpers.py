"""Shared test doubles for fetch-engine tests."""

from __future__ import annotations

from europagrad_agent.engines.base import FetchResult
from html_fixtures import PROGRAM_HTML


class ScriptedEngine:
    """Test double returning scripted results/errors in order."""

    def __init__(self, name: str, results: list[FetchResult | Exception]) -> None:
        self.name = name
        self._results = list(results)
        self.calls: list[str] = []

    async def fetch(self, url: str) -> FetchResult:
        self.calls.append(url)
        item = self._results.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(engine: str, html: str = PROGRAM_HTML) -> FetchResult:
    return FetchResult(
        url="https://x.edu/p", status=200, engine=engine, html=html, text_chars=900, links=[]
    )


def shell(engine: str) -> FetchResult:
    from html_fixtures import JS_SHELL_HTML

    return FetchResult(
        url="https://x.edu/p", status=200, engine=engine, html=JS_SHELL_HTML, text_chars=30, links=[]
    )
