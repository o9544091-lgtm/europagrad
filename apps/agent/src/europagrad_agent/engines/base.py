"""Engine contracts for the adaptive fetch router (tasks 6-7).

Every fetch engine implements FetchEngine.fetch(url) and returns a FetchResult.
Quality heuristics live in engines.quality; routing memory lives in
engines.router via the DomainStats interface implemented in storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    engine: str  # STATIC | PLAYWRIGHT | CRAWL4AI
    html: str = ""
    text_chars: int = 0
    links: list[str] = field(default_factory=list)
    fetch_ms: int = 0

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300 and self.text_chars >= 200


class FetchError(Exception):
    def __init__(self, url: str, engine: str, reason: str) -> None:
        super().__init__(f"{engine} failed for {url}: {reason}")
        self.url = url
        self.engine = engine
        self.reason = reason


class FetchEngine(Protocol):
    name: str

    async def fetch(self, url: str) -> FetchResult: ...
