"""LLM extraction service (task 10): OpenAI-compatible chat completions, JSON mode.

Works with any OpenAI-compatible gateway: OpenRouter (default), OpenCode Zen,
direct provider endpoints — configured via LLM_BASE_URL + OPENROUTER_MODEL +
OPENROUTER_API_KEY (the key name is historical; any gateway key goes there).

The prompt forces the model to fill CitedValue fields with VERBATIM quotes
copied from the provided page text. ExtractionValidator then re-verifies every
quote against the content — fabricated quotes are dropped, so uncited facts
can never reach storage.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from europagrad_agent.config import get_settings
from europagrad_agent.extraction.schemas import ExtractionBundle, ExtractionValidator

DEFAULT_LLM_BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = """You are a precise data-extraction engine for university admissions research.
You receive the text of one official web page and must extract structured facts.

STRICT RULES:
1. For every field you fill, copy a VERBATIM quote (max 40 words) from the page text
   into "quote" — exactly as written, no paraphrasing.
2. Set "source_url" to the page URL you were given.
3. If a fact is NOT stated on the page, set the field to null. NEVER guess.
4. Never use outside knowledge. The page is your only source.
5. Respond with a single JSON object matching the requested schema, nothing else."""


class ExtractionService:
    name = "LLM"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = model or settings.openrouter_model
        self._base_url = (base_url or settings.llm_base_url or DEFAULT_LLM_BASE_URL).rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=90.0)

    async def extract(self, url: str, page_text: str, target: str = "program") -> tuple[ExtractionBundle, list[str]]:
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY not configured")

        user_prompt = (
            f"Page URL: {url}\n\n"
            f"Extract the {target} information from this page text:\n\n"
            f"{page_text[:24000]}\n\n"
            "JSON schema to fill (null for anything not stated):\n"
            '{\n'
            '  "program": {"program_name": {"value": str, "source_url": str, "quote": str} | null, '
            '"degree": same|null, "language": same|null, "duration_months": {"value": int,...}|null, '
            '"tuition_eur_per_year": {"value": {"amount_eur": number|null, "note": str},...}|null, '
            '"ielts_overall": {"value": number,...}|null, "moi_accepted": {"value": bool,...}|null, '
            '"application_deadline": {"value": str(YYYY-MM-DD),...}|null, '
            '"scholarship_note": {"value": str,...}|null, "part_time_work": {"value": str,...}|null, '
            '"field_tags": [str]},\n'
            '  "scholarship": null or {"name": cited|null, "provider_type": cited|null, '
            '"stipend_monthly_eur": cited|null, "covers_tuition": cited|null, '
            '"bangladesh_eligible": cited|null, "deadline": cited|null, '
            '"requires_admission_first": cited|null, "notes": [str]}\n'
            "}"
        )

        resp = await self._client.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        if resp.status_code == 429:
            raise RuntimeError("llm gateway rate limit exceeded")
        if resp.status_code >= 400:
            raise RuntimeError(f"llm gateway error {resp.status_code}: {resp.text[:200]}")

        content: str = resp.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)
        bundle = _bundle_from_payload(url, payload)
        cleaned, rejected = ExtractionValidator.validate(bundle, page_text)
        return cleaned, rejected


def _bundle_from_payload(url: str, payload: dict[str, Any]) -> ExtractionBundle:
    """Tolerant parse: model JSON -> ExtractionBundle. Malformed fields become None."""
    program_payload = payload.get("program") or {}
    scholarship_payload = payload.get("scholarship")

    def fix_cited(obj: Any) -> Any:
        if not isinstance(obj, dict):
            return None
        out = dict(obj)
        out.setdefault("source_url", url)
        return out

    for key in ("program_name", "degree", "language", "duration_months", "tuition_eur_per_year",
                "ielts_overall", "moi_accepted", "application_deadline", "scholarship_note", "part_time_work"):
        if key in program_payload:
            program_payload[key] = fix_cited(program_payload[key])
    program_payload.setdefault("source_url", url)

    if isinstance(scholarship_payload, dict):
        for key in ("name", "provider_type", "stipend_monthly_eur", "covers_tuition",
                    "bangladesh_eligible", "deadline", "requires_admission_first"):
            if key in scholarship_payload:
                scholarship_payload[key] = fix_cited(scholarship_payload[key])
        scholarship_payload.setdefault("source_url", url)

    return ExtractionBundle.model_validate({"program": program_payload, "scholarship": scholarship_payload})
