"""Task 10 tests: citation enforcement — the anti-hallucination core."""

from __future__ import annotations

import json

import httpx
import pytest

from europagrad_agent.extraction.schemas import (
    CitationError,
    CitedValue,
    ExtractionBundle,
    ExtractionValidator,
    ProgramExtraction,
    quote_in_content,
)
from europagrad_agent.extraction.service import ExtractionService, _bundle_from_payload

PAGE = (
    "MSc Computer Science. The programme is taught entirely in English and takes 24 months to "
    "complete. Tuition fees for non-EU students are EUR 2,000 per year. IELTS 6.5 overall with "
    "no band below 6.0 is required. Application deadline: 15 March 2027. Students may work "
    "part-time up to 20 hours per week during lectures."
)


def cited(value, quote: str) -> CitedValue:
    return CitedValue(value=value, source_url="https://uni.edu/msc-cs", quote=quote)


class TestQuoteMatching:
    def test_exact_substring(self) -> None:
        assert quote_in_content("IELTS 6.5 overall", PAGE) is True

    def test_whitespace_normalized(self) -> None:
        assert quote_in_content("taught entirely in\n English", PAGE.replace("in English", "in\n  English")) is True

    def test_case_insensitive(self) -> None:
        assert quote_in_content("ielts 6.5 overall", PAGE) is True

    def test_fabricated_quote_rejected(self) -> None:
        assert quote_in_content("Tuition is free for all students", PAGE) is False

    def test_empty_quote_rejected(self) -> None:
        assert quote_in_content("", PAGE) is False


class TestCitedValue:
    def test_validate_against_passes(self) -> None:
        cited("24", "takes 24 months to\ncomplete").validate_against(PAGE)

    def test_validate_against_raises_on_fabrication(self) -> None:
        with pytest.raises(CitationError, match="quote not found"):
            cited(5000, "Tuition costs EUR 5,000 per year").validate_against(PAGE)


def bundle_with(tuition_quote: str) -> ExtractionBundle:
    return ExtractionBundle(
        program=ProgramExtraction(
            source_url="https://uni.edu/msc-cs",
            program_name=cited("MSc Computer Science", "MSc Computer Science"),
            duration_months=cited(24, "takes 24 months to complete"),
            tuition_eur_per_year=cited({"amount_eur": 5000.0, "note": ""}, tuition_quote),
            ielts_overall=cited(6.5, "IELTS 6.5 overall"),
        )
    )


class TestExtractionValidator:
    def test_valid_bundle_unchanged(self) -> None:
        bundle = bundle_with("EUR 2,000 per year")
        cleaned, rejected = ExtractionValidator.validate(bundle, PAGE)
        assert rejected == []
        assert cleaned.program.tuition_eur_per_year is not None

    def test_fabricated_field_dropped_others_kept(self) -> None:
        bundle = bundle_with("Tuition costs EUR 5,000 per year")
        cleaned, rejected = ExtractionValidator.validate(bundle, PAGE)
        assert rejected == ["program.tuition_eur_per_year"]
        assert cleaned.program.tuition_eur_per_year is None
        assert cleaned.program.ielts_overall is not None
        assert cleaned.program.duration_months is not None

    def test_all_fields_fabricated_all_dropped(self) -> None:
        bundle = ExtractionBundle(
            program=ProgramExtraction(
                source_url="https://uni.edu/x",
                program_name=cited("Fake Program", "This program does not exist"),
            )
        )
        cleaned, rejected = ExtractionValidator.validate(bundle, PAGE)
        assert rejected == ["program.program_name"]
        assert cleaned.program.program_name is None


class TestBundleFromPayload:
    def test_tolerant_parse_missing_source_url(self) -> None:
        payload = {
            "program": {
                "program_name": {"value": "MSc CS", "quote": "MSc Computer Science"},
                "field_tags": [" CS ", ""],
            },
            "scholarship": None,
        }
        bundle = _bundle_from_payload("https://uni.edu/p", payload)
        assert bundle.program.source_url == "https://uni.edu/p"
        assert bundle.program.program_name is not None
        assert bundle.program.program_name.source_url == "https://uni.edu/p"
        assert bundle.program.field_tags == ["cs"]

    def test_malformed_cited_becomes_none(self) -> None:
        bundle = _bundle_from_payload("https://u.edu/p", {"program": {"ielts_overall": "not-a-dict"}})
        assert bundle.program.ielts_overall is None


class TestExtractionService:
    async def test_mocked_llm_flow_end_to_end(self) -> None:
        llm_json = {
            "program": {
                "program_name": {"value": "MSc Computer Science", "source_url": "https://uni.edu/msc-cs", "quote": "MSc Computer Science"},
                "ielts_overall": {"value": 6.5, "source_url": "https://uni.edu/msc-cs", "quote": "IELTS 6.5 overall"},
                "tuition_eur_per_year": {"value": {"amount_eur": 9999.0, "note": ""}, "source_url": "https://uni.edu/msc-cs", "quote": "Tuition is EUR 9,999 per year"},
            },
            "scholarship": None,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["temperature"] == 0
            assert body["model"]
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(llm_json)}}]})

        service = ExtractionService(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), model="test-model")
        # inject key without touching env
        object.__setattr__(service, "_api_key", "test-key")

        cleaned, rejected = await service.extract("https://uni.edu/msc-cs", PAGE)
        assert rejected == ["program.tuition_eur_per_year"]
        assert cleaned.program.program_name is not None
        assert cleaned.program.ielts_overall is not None
        assert cleaned.program.tuition_eur_per_year is None

    async def test_custom_gateway_base_url(self) -> None:
        llm_json = {
            "program": {
                "program_name": {"value": "MSc CS", "source_url": "https://uni.edu/msc-cs", "quote": "MSc Computer Science"},
            },
            "scholarship": None,
        }
        seen_urls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_urls.append(str(request.url))
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(llm_json)}}]})

        service = ExtractionService(
            client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            model="nemotron-free",
            base_url="https://opencode.ai/zen/v1",
        )
        object.__setattr__(service, "_api_key", "zen-key")

        cleaned, rejected = await service.extract("https://uni.edu/msc-cs", PAGE)
        assert seen_urls[0] == "https://opencode.ai/zen/v1/chat/completions"
        assert cleaned.program.program_name is not None
        assert rejected == []

    async def test_missing_key_raises(self) -> None:
        service = ExtractionService(client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))))
        object.__setattr__(service, "_api_key", "")
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            await service.extract("https://u.edu", "text")
