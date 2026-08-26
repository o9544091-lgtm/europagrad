"""Domain engine-memory: persists best engine + failure counts (task 6).

SupabaseDomainStats writes to domain_fetch_stats via service role.
MemoryDomainStats is the test/local fallback.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from supabase import create_client

from europagrad_agent.config import get_settings


class DomainStats(Protocol):
    async def get_best(self, domain: str) -> str | None: ...

    async def record_success(self, domain: str, engine: str) -> None: ...

    async def record_failure(self, domain: str, engine: str) -> None: ...


class MemoryDomainStats:
    def __init__(self) -> None:
        self._best: dict[str, str] = {}
        self._static_failures: dict[str, int] = {}
        self._playwright_failures: dict[str, int] = {}
        self._last_success: dict[str, datetime] = {}

    async def get_best(self, domain: str) -> str | None:
        return self._best.get(domain)

    async def record_success(self, domain: str, engine: str) -> None:
        self._best[domain] = engine
        self._last_success[domain] = datetime.now(UTC)

    async def record_failure(self, domain: str, engine: str) -> None:
        if engine == "STATIC":
            self._static_failures[domain] = self._static_failures.get(domain, 0) + 1
        elif engine == "PLAYWRIGHT":
            self._playwright_failures[domain] = self._playwright_failures.get(domain, 0) + 1


class SupabaseDomainStats:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError("SupabaseDomainStats requires SUPABASE_URL + SUPABASE_SERVICE_KEY")
        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    async def get_best(self, domain: str) -> str | None:
        rows = self._client.table("domain_fetch_stats").select("best_engine").eq("domain", domain).maybe_single().execute()
        data = getattr(rows, "data", rows)
        return data.get("best_engine") if data else None

    async def record_success(self, domain: str, engine: str) -> None:
        self._client.table("domain_fetch_stats").upsert(
            {
                "domain": domain,
                "best_engine": engine,
                "last_success": datetime.now(UTC).isoformat(),
            },
            on_conflict="domain",
        ).execute()

    async def record_failure(self, domain: str, engine: str) -> None:
        column = {"STATIC": "static_failures", "PLAYWRIGHT": "playwright_failures"}.get(engine)
        if column is None:
            return
        current = (
            self._client.table("domain_fetch_stats")
            .select(column)
            .eq("domain", domain)
            .maybe_single()
            .execute()
        )
        count = (current.data or {}).get(column, 0) or 0
        self._client.table("domain_fetch_stats").upsert(
            {"domain": domain, column: count + 1}, on_conflict="domain"
        ).execute()
