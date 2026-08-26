"""Task 8 tests: ROR loader, sitemap harvester, depth profiles."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from europagrad_agent.registries.depth import get_profile
from europagrad_agent.registries.ror import (
    RorLoader,
    domain_from_url,
    merge_institutions,
    parse_ror_item,
)
from europagrad_agent.registries.sitemap import SitemapHarvester

FIXTURES = Path(__file__).parent / "fixtures"
SITEMAP_INDEX = (FIXTURES / "sitemap_index.xml").read_bytes()
SITEMAP_URLS = (FIXTURES / "sitemap_urls.xml").read_bytes()


def ror_item(name: str, ror_id: str, url: str, types: list[str]) -> dict:
    return {
        "id": ror_id,
        "name": name,
        "types": types,
        "links": [url],
        "addresses": [{"country_code": "EE"}],
    }


class TestRorParsing:
    def test_education_item_parsed(self) -> None:
        inst = parse_ror_item(
            ror_item("University of Tartu", "https://ror.org/01jrjn955", "https://ut.ee", ["Education"])
        )
        assert inst is not None
        assert inst.name == "University of Tartu"
        assert inst.country == "EE"
        assert inst.domain == "ut.ee"

    def test_non_education_filtered(self) -> None:
        assert parse_ror_item(ror_item("ACME Corp", "https://ror.org/x", "https://acme.io", ["Company"])) is None

    def test_www_stripped_from_domain(self) -> None:
        assert domain_from_url("https://www.ut.ee/en") == "ut.ee"
        assert domain_from_url("ut.ee") == "ut.ee"
        assert domain_from_url(None) is None


class TestRorLoader:
    async def test_pagination_and_dedupe(self) -> None:
        page1 = {
            "items": [
                ror_item("University of Tartu", "https://ror.org/a", "https://ut.ee", ["Education"]),
                ror_item("Tallinn University of Technology", "https://ror.org/b", "https://taltech.ee", ["Education"]),
            ],
            "meta": {"next": "c1"},
        }
        page2 = {
            "items": [
                ror_item("University of Tartu", "https://ror.org/a", "https://ut.ee", ["Education"]),
                ror_item("Estonian Business School", "https://ror.org/c", "https://ebs.ee", ["Education"]),
            ],
            "meta": {"next": None},
        }

        def handler(request: httpx.Request) -> httpx.Response:
            cursor = request.url.params.get("cursor")
            return httpx.Response(200, json=page2 if cursor == "c1" else page1)

        loader = RorLoader(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        institutions = await loader.load_country("EE")
        names = {i.name for i in institutions}
        assert names == {"University of Tartu", "Tallinn University of Technology", "Estonian Business School"}


class TestMerge:
    def test_merge_enriches_without_duplicates(self) -> None:
        a = [
            parse_ror_item(ror_item("Uni A", "https://ror.org/a", None, ["Education"])),
            parse_ror_item(ror_item("Uni B", "https://ror.org/b", "https://b.edu", ["Education"])),
        ]
        b = [
            parse_ror_item(ror_item("Uni A", "https://ror.org/a", "https://a.edu", ["Education"])),
        ]
        merged = merge_institutions(a, b)
        assert len(merged) == 2
        uni_a = next(i for i in merged if i.name == "Uni A")
        assert uni_a.domain == "a.edu"


class TestSitemapHarvester:
    async def test_index_expansion_and_keyword_filter(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nAllow: /\n")
            if path == "/sitemap.xml":
                return httpx.Response(200, content=SITEMAP_INDEX)
            if path == "/sitemap-programmes.xml":
                return httpx.Response(200, content=SITEMAP_URLS)
            return httpx.Response(404)

        harvester = SitemapHarvester(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        result = await harvester.harvest("uni.edu", cap=50)

        assert result.sitemap_found is True
        assert result.total_urls_seen == 7
        assert "https://uni.edu/en/msc-computer-science" in result.candidates
        assert "https://uni.edu/en/admissions/international" in result.candidates
        assert "https://uni.edu/en/tuition-fees" in result.candidates
        assert "https://uni.edu/en/scholarships" in result.candidates
        assert "https://uni.edu/en/campus-life" not in result.candidates
        assert "https://uni.edu/files/brochure.pdf" not in result.candidates

    async def test_cap_enforced(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nAllow: /\n")
            if request.url.path == "/sitemap.xml":
                return httpx.Response(200, content=SITEMAP_URLS)
            return httpx.Response(404)

        harvester = SitemapHarvester(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        result = await harvester.harvest("uni.edu", cap=2)
        assert len(result.candidates) == 2

    async def test_missing_sitemap_returns_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nAllow: /\n")
            return httpx.Response(404)

        harvester = SitemapHarvester(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        result = await harvester.harvest("none.edu")
        assert result.sitemap_found is False
        assert result.candidates == []

    async def test_robots_disallowed_short_circuits(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
            raise AssertionError("should not fetch anything else")

        harvester = SitemapHarvester(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        result = await harvester.harvest("blocked.edu")
        assert result.sitemap_found is False
        assert result.candidates == []


class TestDepthProfiles:
    def test_all_levels_defined(self) -> None:
        l1, l2, l3 = get_profile("L1"), get_profile("l2"), get_profile("L3")
        assert l1.search_pages_max == 3 and l1.domain_page_cap == 15
        assert l2.search_pages_max == 6 and l2.sitemap_mode == "all_universities"
        assert l3.search_pages_max == 10 and l3.domain_page_cap == 100

    def test_unknown_level_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown depth"):
            get_profile("L9")
