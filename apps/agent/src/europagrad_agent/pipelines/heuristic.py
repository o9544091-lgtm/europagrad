"""Heuristic extractor (task 12): keyless extraction for pipeline validation.

Builds CitedValue fields from verbatim sentences found in fetched text, then
runs the same ExtractionValidator gate as the LLM path — quotes are verbatim
by construction. Quality is placeholder-grade (QC flags non-CSE hits for
review); production extraction uses the LLM path (task 13).
"""

from __future__ import annotations

import contextlib
import re

from selectolax.parser import HTMLParser

from europagrad_agent.extraction.schemas import (
    CitedValue,
    ExtractionBundle,
    ExtractionValidator,
    ProgramExtraction,
)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if 20 < len(s.strip()) < 300]


def _html_to_text(html: str) -> str:
    try:
        tree = HTMLParser(html)
    except Exception:
        return ""
    with contextlib.suppress(Exception):
        for node in tree.css("script, style, nav, header, footer"):
            node.decompose()
    body = tree.body
    raw = body.text(separator=" ", strip=True) if body else ""
    return re.sub(r"\s+", " ", raw)


def _find_sentence(sentences: list[str], pattern: str) -> tuple[str, str] | None:
    for s in sentences:
        m = re.search(pattern, s, re.IGNORECASE)
        if m:
            return (m.group(1) if m.groups() else m.group(0)), s
    return None


class HeuristicExtractor:
    name = "HEURISTIC"

    async def extract(self, url: str, page_text: str, target: str = "program") -> tuple[ExtractionBundle, list[str]]:
        text = _html_to_text(page_text)
        fields: dict = {"source_url": url}

        if len(text) >= 300:
            sentences = _sentences(text)

            h1_text = None
            try:
                node = HTMLParser(page_text).css_first("h1")
                h1_text = node.text(strip=True) if node else None
            except Exception:
                h1_text = None
            if h1_text and 5 < len(h1_text) < 120 and h1_text in text:
                fields["program_name"] = CitedValue(
                    value=h1_text.strip(), source_url=url, quote=h1_text.strip()
                )

            ielts = _find_sentence(sentences, r"IELTS[^.\d]{0,20}(\d\.\d)")
            if ielts:
                fields["ielts_overall"] = CitedValue(
                    value=float(ielts[0]), source_url=url, quote=ielts[1][:200]
                )

            duration = _find_sentence(sentences, r"(\d{1,2})\s+(?:months|month)")
            if duration:
                fields["duration_months"] = CitedValue(
                    value=int(duration[0]), source_url=url, quote=duration[1][:200]
                )

            tuition = _find_sentence(sentences, r"(?:EUR|€)\s*([\d.,]{3,12})")
            if tuition:
                raw = tuition[0]
                amount = float(raw.replace(".", "").replace(",", "")) if "," in raw else float(raw)
                fields["tuition_eur_per_year"] = CitedValue(
                    value={"amount_eur": amount, "note": "heuristic pass"},
                    source_url=url,
                    quote=tuition[1][:200],
                )

            deadline = _find_sentence(sentences, r"deadline[:\s]+([^.;]{6,40})")
            if deadline:
                fields["application_deadline"] = CitedValue(
                    value=deadline[0].strip(), source_url=url, quote=deadline[1][:200]
                )

            tags = []
            for tag, pattern in (
                ("cs", r"computer science"),
                ("ai", r"artificial intelligence"),
                ("data-science", r"data science"),
                ("software-engineering", r"software engineering"),
            ):
                if re.search(pattern, text, re.IGNORECASE):
                    tags.append(tag)
            if tags:
                fields["field_tags"] = tags

        bundle = ExtractionBundle(program=ProgramExtraction.model_validate(fields))
        return ExtractionValidator.validate(bundle, page_text)
