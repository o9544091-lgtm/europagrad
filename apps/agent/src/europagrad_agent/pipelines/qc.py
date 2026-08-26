"""QC gate (task 11): spec §42 checklist encoded as assertions + warnings."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from europagrad_agent.extraction.schemas import CitedValue, ExtractionBundle
from europagrad_agent.registries.ror import Institution

CSE_HINTS = (
    "computer", "software", "data science", "artificial intelligence", "machine learning",
    "information", "cyber", "security", "it ", "informatics", "engineering", "ai",
)

CSE_TAG_SET = {
    "cs", "ai", "ml", "data-science", "software-engineering", "cybersecurity",
    "information-systems", "it", "robotics", "computer-engineering", "embedded",
    "hci", "systems",
}


def is_cse_relevant(bundle: ExtractionBundle) -> bool:
    """Hard relevance bar for storage (spec §42: program relevant to background).
    A program must show CSE signal via field tags or its name — otherwise the
    orchestrator skips it entirely (off-target programs never reach the DB)."""
    program = bundle.program
    if any(tag in CSE_TAG_SET for tag in program.field_tags):
        return True
    name = program.program_name.value.lower() if program.program_name else ""
    return any(hint in name for hint in CSE_HINTS)

DATE_PATTERNS = (r"\d{4}-\d{2}-\d{2}", r"\d{1,2}\s+\w+\s+\d{4}")


@dataclass
class QCReport:
    entity: str
    passed: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def fail(self, msg: str) -> None:
        self.errors.append(msg)
        self.passed = False


CITED_FIELDS = (
    "program_name", "degree", "language", "duration_months", "tuition_eur_per_year",
    "ielts_overall", "moi_accepted", "application_deadline", "scholarship_note", "part_time_work",
)


def check_program(bundle: ExtractionBundle, institution: Institution) -> QCReport:
    report = QCReport(entity=f"{institution.name}::program")

    program = bundle.program
    if program.program_name is None:
        report.fail("no program name extracted — nothing to store")
        return report

    # Relevance: is this plausibly CSE-relevant? (spec §42: program relevant to background)
    name_and_tags = " ".join(
        [program.program_name.value.lower() if program.program_name else ""]
        + list(program.field_tags)
    )
    if not any(hint in name_and_tags for hint in CSE_HINTS):
        report.warn(f"not obviously CSE-relevant: '{name_and_tags[:60]}' — flag for review, keep with low relevance")

    # Deadline currency (spec §42: intake/deadline current)
    deadline = program.application_deadline
    if deadline is not None:
        raw = deadline.value
        if not any(re.search(p, raw) for p in DATE_PATTERNS):
            report.warn(f"deadline not parseable as date: '{raw}'")
        else:
            years = {int(y) for y in re.findall(r"(20\d{2})", raw)}
            current_year = datetime.now(UTC).year
            if years and max(years) < current_year:
                report.warn(f"deadline appears stale ({raw}) — will store as CLOSED")

    # Funding claims must be cited (schema enforces citations; double-check semantics)
    tuition = program.tuition_eur_per_year
    if tuition is not None and tuition.value.amount_eur == 0 and not tuition.value.note:
        report.warn("tuition zero claimed with no explanatory note — verify waiver vs free-programme")

    # Uncited facts cannot exist by construction; assert defensively
    for fname in CITED_FIELDS:
        value = getattr(program, fname)
        if value is not None and not isinstance(value, CitedValue):
            report.fail(f"internal: field {fname} lost its citation wrapper")

    return report


def check_duplicates(existing_keys: set[tuple], key: tuple) -> list[str]:
    """Returns warnings if key collides with an existing dedupe key."""
    if key in existing_keys:
        return [f"duplicate detected for key {key} — upsert will update in place"]
    return []
