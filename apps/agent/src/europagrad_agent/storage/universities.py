"""University persistence: find-by-name or insert (task 11)."""

from __future__ import annotations

from supabase import create_client

from europagrad_agent.config import get_settings
from europagrad_agent.registries.ror import Institution


class UniversityStore:
    """ensure_university: find by country+name or insert; returns programs FK id."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError("UniversityStore requires SUPABASE_URL + SUPABASE_SERVICE_KEY")
        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    async def ensure_university(self, institution: Institution) -> str:
        existing = await self.get_university_id(institution)
        if existing:
            return existing
        inserted = (
            self._client.table("universities")
            .insert({
                "name": institution.name,
                "country_id": institution.country,
                "website": institution.homepage,
                "registry_ids": {"ror": institution.ror_id} if institution.ror_id else {},
                "type": "PUBLIC",
            })
            .execute()
        )
        return inserted.data[0]["id"]

    async def get_university_id(self, institution: Institution) -> str | None:
        found = (
            self._client.table("universities")
            .select("id")
            .eq("country_id", institution.country)
            .ilike("name", institution.name)
            .limit(1)
            .execute()
        )
        return found.data[0]["id"] if found.data else None
