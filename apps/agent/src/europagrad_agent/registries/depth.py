"""Depth level profiles (task 8): L1/L2/L3 caps for search pages, sitemap breadth, page limits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DepthLevel = Literal["L1", "L2", "L3"]


@dataclass(frozen=True)
class DepthProfile:
    level: DepthLevel
    search_pages_max: int
    sitemap_mode: Literal["portals_only", "all_universities", "full_sitemaps"]
    domain_page_cap: int
    registry_sources: Literal["national_only", "national_ror", "national_ror_eter"]


PROFILES: dict[DepthLevel, DepthProfile] = {
    "L1": DepthProfile("L1", search_pages_max=3, sitemap_mode="portals_only", domain_page_cap=15, registry_sources="national_only"),
    "L2": DepthProfile("L2", search_pages_max=6, sitemap_mode="all_universities", domain_page_cap=40, registry_sources="national_ror"),
    "L3": DepthProfile("L3", search_pages_max=10, sitemap_mode="full_sitemaps", domain_page_cap=100, registry_sources="national_ror_eter"),
}


def get_profile(level: str) -> DepthProfile:
    try:
        return PROFILES[level.upper()]  # type: ignore[assignment]
    except KeyError as err:
        raise ValueError(f"Unknown depth level: {level} (use L1, L2, or L3)") from err
