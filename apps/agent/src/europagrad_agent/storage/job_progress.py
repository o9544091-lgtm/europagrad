"""research_jobs progress persistence for the orchestrator (task 11)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from supabase import create_client

from europagrad_agent.config import get_settings


class JobProgress:
    """Creates (or attaches to) a research_jobs row and updates progress through phases."""

    def __init__(
        self,
        countries: list[str],
        depth_level: str,
        triggered_by: str | None = None,
        job_id: str | None = None,
    ) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError("JobProgress requires SUPABASE_URL + SUPABASE_SERVICE_KEY")
        self._client = create_client(settings.supabase_url, settings.supabase_service_key)
        self.job_id = job_id or str(uuid.uuid4())
        if job_id:
            self._client.table("research_jobs").update({
                "status": "RUNNING",
                "started_at": datetime.now(UTC).isoformat(),
                "progress": {"phase": "attach"},
            }).eq("id", job_id).execute()
        else:
            self._client.table("research_jobs").insert({
                "id": self.job_id,
                "triggered_by": triggered_by,
                "countries": countries,
                "depth_level": depth_level,
                "status": "RUNNING",
                "progress": {},
                "started_at": datetime.now(UTC).isoformat(),
            }).execute()

    async def update(self, phase: str, done: int, total: int) -> None:
        self._client.table("research_jobs").update({
            "progress": {"phase": phase, "done": done, "total": total,
                         "updated_at": datetime.now(UTC).isoformat()},
        }).eq("id", self.job_id).execute()

    def finish(self, status: str, error: str | None = None, summary: dict | None = None) -> None:
        self._client.table("research_jobs").update({
            "status": status,
            "error": error,
            "progress": summary or {},
            "finished_at": datetime.now(UTC).isoformat(),
        }).eq("id", self.job_id).execute()


class MemoryJobProgress:
    """Test/local fallback with the same interface."""

    def __init__(self, countries: list[str], depth_level: str, triggered_by: str | None = None) -> None:
        self.job_id = "memory-job"
        self.updates: list[tuple[str, int, int]] = []
        self.final: tuple[str, str | None, dict | None] | None = None

    async def update(self, phase: str, done: int, total: int) -> None:
        self.updates.append((phase, done, total))

    def finish(self, status: str, error: str | None = None, summary: dict | None = None) -> None:
        self.final = (status, error, summary)
