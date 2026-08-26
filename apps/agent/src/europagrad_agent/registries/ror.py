"""University inventory from official registries (task 8).

Primary loader: ROR (Research Organization Registry) public API — uniform
coverage of all 30+ countries, no API key. National registries (Hochschulkompass,
Universitaly, ...) are configured as supplements; their scraped lists can be
merged via merge_institutions().

Acceptance target: >=95% recall of accredited institutions for a country.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlsplit

import httpx

ROR_API = "https://api.ror.org/organizations"
PAGE_SIZE = 1000  # ROR max


@dataclass(frozen=True)
class Institution:
    name: str
    country: str  # ISO2
    domain: str | None
    ror_id: str | None = None
    eter_id: str | None = None
    national_id: str | None = None
    types: tuple[str, ...] = field(default_factory=tuple)

    @property
    def homepage(self) -> str | None:
        return f"https://{self.domain}" if self.domain else None


EDUCATION_TYPES = {"Education", "Education/Qac", "Company", "Facility"}


def domain_from_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url if "://" in url else f"https://{url}")
    host = parts.netloc or parts.path.split("/")[0]
    host = host.lower().removeprefix("www.")
    return host or None


def parse_ror_item(item: dict) -> Institution | None:
    types = set(item.get("types", []))
    if not types & {"Education"}:
        return None
    country_code = (item.get("addresses") or [{}])[0].get("country_code", "")
    links = item.get("links") or []
    domain = domain_from_url(links[0]) if links else None
    return Institution(
        name=item.get("name", "").strip(),
        country=country_code,
        domain=domain,
        ror_id=item.get("id"),
        types=tuple(sorted(types)),
    )


class RorLoader:
    """Cursor-paginated ROR API loader. Hermetic tests use a mock transport."""

    def __init__(self, client: httpx.AsyncClient | None = None, api_base: str = ROR_API) -> None:
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._api_base = api_base

    async def load_country(self, iso2: str) -> list[Institution]:
        out: list[Institution] = []
        cursor: str | None = None
        while True:
            params: dict[str, str | int] = {"countries": iso2.upper(), "page": PAGE_SIZE}
            if cursor:
                params["cursor"] = cursor
            resp = await self._client.get(self._api_base, params=params)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                inst = parse_ror_item(item)
                if inst:
                    out.append(inst)
            cursor = data.get("meta", {}).get("next")
            if not cursor:
                break
        return _dedupe(out)


def _dedupe(institutions: list[Institution]) -> list[Institution]:
    seen: set[tuple[str, str]] = set()
    out: list[Institution] = []
    for inst in institutions:
        key = (inst.name.lower(), inst.country)
        if key in seen:
            continue
        seen.add(key)
        out.append(inst)
    return out


def merge_institutions(*sources: list[Institution]) -> list[Institution]:
    """Union by name+country; later sources enrich earlier (ids, domains)."""
    merged: dict[tuple[str, str], Institution] = {}
    for source in sources:
        for inst in source:
            key = (inst.name.lower(), inst.country)
            if key not in merged:
                merged[key] = inst
                continue
            base = merged[key]
            merged[key] = Institution(
                name=base.name,
                country=base.country,
                domain=base.domain or inst.domain,
                ror_id=base.ror_id or inst.ror_id,
                eter_id=base.eter_id or inst.eter_id,
                national_id=base.national_id or inst.national_id,
                types=base.types or inst.types,
            )
    return sorted(merged.values(), key=lambda i: i.name.lower())
