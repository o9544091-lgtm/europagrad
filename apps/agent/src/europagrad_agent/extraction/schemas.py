"""Pydantic extraction schemas with MANDATORY citations (task 10).

Anti-hallucination contract (AGENTS.md golden rules 1-2):
- Every critical field is a CitedValue: {value, source_url, quote}.
- The quote must be a verbatim substring of the fetched page content
  (validated at >= 0.95 similarity after whitespace normalization).
- A field without a valid citation is stored as NOT_SPECIFIED — never guessed.
- Conflicts are captured, never silently resolved.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from pydantic import BaseModel, ConfigDict, Field, field_validator

NOT_SPECIFIED = "NOT_SPECIFIED"


class CitationError(ValueError):
    pass


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_in_content(quote: str, content: str, min_ratio: float = 0.95) -> bool:
    q = normalize_ws(quote)
    if not q:
        return False
    if q in normalize_ws(content):
        return True
    # sliding window fuzzy check for minor whitespace/punctuation drift
    window = len(q) * 2
    content_norm = normalize_ws(content)
    for start in range(0, max(len(content_norm) - len(q), 1), max(window // 2, 1)):
        segment = content_norm[start : start + window]
        if not segment:
            break
        if SequenceMatcher(None, q, segment).ratio() >= min_ratio and q[: 30] in segment:
            return True
    return False


class CitedValue[T](BaseModel):
    model_config = ConfigDict(frozen=True)
    value: T
    source_url: str
    quote: str

    def validate_against(self, content: str) -> None:
        if not quote_in_content(self.quote, content):
            raise CitationError(
                f"quote not found in content for value={self.value!r} (url={self.source_url})"
            )


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)
    amount_eur: float | None = None
    note: str = ""


class ProgramExtraction(BaseModel):
    """Fields extracted from ONE program page (one source document)."""

    model_config = ConfigDict(frozen=True)
    source_url: str
    program_name: CitedValue[str] | None = None
    degree: CitedValue[str] | None = None
    language: CitedValue[str] | None = None
    duration_months: CitedValue[int] | None = None
    tuition_eur_per_year: CitedValue[Money] | None = None
    ielts_overall: CitedValue[float] | None = None
    moi_accepted: CitedValue[bool] | None = None
    application_deadline: CitedValue[str] | None = None
    scholarship_note: CitedValue[str] | None = None
    part_time_work: CitedValue[str] | None = None
    field_tags: list[str] = Field(default_factory=list)
    raw_conflicts: list[str] = Field(default_factory=list)

    @field_validator("field_tags", mode="before")
    @classmethod
    def _lower_tags(cls, v: list[str]) -> list[str]:
        return [str(t).lower().strip() for t in v if str(t).strip()]


class ScholarshipExtraction(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_url: str
    name: CitedValue[str] | None = None
    provider_type: CitedValue[str] | None = None
    stipend_monthly_eur: CitedValue[float] | None = None
    covers_tuition: CitedValue[bool] | None = None
    bangladesh_eligible: CitedValue[bool] | None = None
    deadline: CitedValue[str] | None = None
    requires_admission_first: CitedValue[bool] | None = None
    notes: list[str] = Field(default_factory=list)


class ExtractionBundle(BaseModel):
    program: ProgramExtraction
    scholarship: ScholarshipExtraction | None = None


class ExtractionValidator:
    """Validates an LLM-produced bundle against the fetched page content.

    Returns (cleaned_bundle, rejected_field_names). A field whose quote fails
    validation is dropped (becomes None => NOT_SPECIFIED upstream)."""

    @staticmethod
    def validate(bundle: ExtractionBundle, content: str) -> tuple[ExtractionBundle, list[str]]:
        rejected: list[str] = []

        program = bundle.program
        p_updates: dict = {}
        for fname in type(program).model_fields:
            value = getattr(program, fname)
            if isinstance(value, CitedValue):
                try:
                    value.validate_against(content)
                except CitationError:
                    rejected.append(f"program.{fname}")
                    p_updates[fname] = None
        program = program.model_copy(update=p_updates)

        scholarship = bundle.scholarship
        if scholarship is not None:
            s_updates: dict = {}
            for fname in type(scholarship).model_fields:
                value = getattr(scholarship, fname)
                if isinstance(value, CitedValue):
                    try:
                        value.validate_against(content)
                    except CitationError:
                        rejected.append(f"scholarship.{fname}")
                        s_updates[fname] = None
            scholarship = scholarship.model_copy(update=s_updates)

        return bundle.model_copy(update={"program": program, "scholarship": scholarship}), rejected
