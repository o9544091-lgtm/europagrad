"""Dataset writers (task 11): idempotent program upsert + change_log diffing.

Dedupe key (docs/data-model.md): (university_id, lower(name), coalesce(deadline,'1900-01-01')).
Re-runs update in place; changed fields append change_log rows; last_verified_at
refreshes only for re-verified fields. CLOSED deadlines update status, never delete.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from supabase import create_client

from europagrad_agent.config import get_settings
from europagrad_agent.extraction.schemas import CitedValue, ExtractionBundle

EVIDENCE_FIELDS = (
    "program_name", "degree", "language", "duration_months", "tuition_eur_per_year",
    "ielts_overall", "moi_accepted", "application_deadline", "scholarship_note", "part_time_work",
)


def parse_deadline(raw: str) -> date | None:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def deadline_status_for(d: date | None) -> str:
    if d is None:
        return "UNKNOWN"
    return "CLOSED" if d < datetime.now(UTC).date() else "OPEN"


class ProgramWriter:
    """Writes programs + evidence + change_log via service role."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError("ProgramWriter requires SUPABASE_URL + SUPABASE_SERVICE_KEY")
        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    async def upsert_program(self, university_id: str, bundle: ExtractionBundle) -> dict:
        """Returns {program_id, created: bool, changed_fields: [..]}."""
        program = bundle.program
        if program.program_name is None:
            raise ValueError("cannot upsert a program without a name")

        row = self._to_row(university_id, program)
        key_name = row["name"].lower()
        deadline = row.get("program_deadline") or "1900-01-01"

        existing = (
            self._client.table("programs")
            .select("id, name, degree, language, duration_months, tuition_eur_per_year, "
                    "ielts, moi_policy, program_deadline, deadline_status, part_time_info, field_tags")
            .eq("university_id", university_id)
            .ilike("name", row["name"])
            .limit(50)
            .execute()
        )
        match = None
        for candidate in existing.data or []:
            if candidate["name"].lower() == key_name and (candidate.get("program_deadline") or "1900-01-01") == deadline:
                match = candidate
                break

        now_iso = datetime.now(UTC).isoformat()
        if match is None:
            inserted = self._client.table("programs").insert(row).execute()
            program_id = inserted.data[0]["id"]
            return {"program_id": program_id, "created": True, "changed_fields": []}

        program_id = match["id"]
        changed: list[str] = []
        update: dict[str, Any] = {}
        for field_name, new_value in row.items():
            old_value = match.get(field_name)
            if self._norm(old_value) != self._norm(new_value):
                update[field_name] = new_value
                changed.append(field_name)
                self._log_change(program_id, field_name, old_value, new_value, program.source_url)
        if update:
            update["last_verified_at"] = now_iso
            self._client.table("programs").update(update).eq("id", program_id).execute()
        else:
            self._client.table("programs").update({"last_verified_at": now_iso}).eq("id", program_id).execute()
        return {"program_id": program_id, "created": False, "changed_fields": changed}

    def _to_row(self, university_id: str, program) -> dict[str, Any]:
        deadline_date = parse_deadline(program.application_deadline.value) if program.application_deadline else None
        moi_policy = None
        if program.moi_accepted is not None:
            moi_policy = "ACCEPTED" if program.moi_accepted.value else "NOT_ACCEPTED"

        evidence = []
        for fname in EVIDENCE_FIELDS:
            value: CitedValue | None = getattr(program, fname)
            if value is None:
                continue
            inner = value.value
            evidence.append({
                "field": fname,
                "value": inner.get("amount_eur") if isinstance(inner, dict) else inner,
                "source_url": value.source_url,
                "quote": value.quote,
                "retrieved_at": datetime.now(UTC).isoformat(),
            })

        ielts = {"overall": program.ielts_overall.value} if program.ielts_overall else None
        tuition = program.tuition_eur_per_year.value.amount_eur if program.tuition_eur_per_year else None

        return {
            "university_id": university_id,
            "name": program.program_name.value if program.program_name else "",
            "degree": program.degree.value if program.degree else None,
            "language": program.language.value if program.language else None,
            "duration_months": program.duration_months.value if program.duration_months else None,
            "tuition_eur_per_year": tuition,
            "ielts": ielts,
            "moi_policy": moi_policy or "NOT_SPECIFIED",
            "program_deadline": deadline_date.isoformat() if deadline_date else None,
            "deadline_status": deadline_status_for(deadline_date),
            "part_time_info": program.part_time_work.value if program.part_time_work else None,
            "field_tags": program.field_tags,
            "evidence": evidence,
            "last_verified_at": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def _norm(value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    def _log_change(self, program_id: str, field_name: str, old: Any, new: Any, source_url: str) -> None:
        source_id = None
        if source_url:
            found = self._client.table("sources").select("id").eq("url", source_url).maybe_single().execute()
            # supabase-py returns APIResponse (data=None) or bare None depending on version
            found_data = getattr(found, "data", found)
            if found_data:
                source_id = found_data["id"]
            else:
                created = self._client.table("sources").insert({"url": source_url, "title": None, "tier": "TIER1_OFFICIAL"}).execute()
                source_id = created.data[0]["id"]
        self._client.table("change_log").insert({
            "entity_type": "program",
            "entity_id": program_id,
            "field": field_name,
            "old_value": old,
            "new_value": new,
            "source_id": source_id,
        }).execute()
