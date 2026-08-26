"""ROR data-dump loader (task 8): complete country inventories, the sanctioned way.

The ROR API explicitly discourages filter-only enumeration (duplicates/omissions
across pages), so full country inventory uses the official Zenodo data dump:
  1. Discover the latest "ROR Data" dataset record on Zenodo.
  2. Download + cache the zip locally (30-day TTL).
  3. Stream the JSON-lines file, filtering types=education + country code.
"""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path

import httpx

from europagrad_agent.registries.ror import Institution

ZENODO_SEARCH = "https://zenodo.org/api/records"
CACHE_TTL_S = 30 * 24 * 3600.0


class RorDumpLoader:
    def __init__(self, client: httpx.AsyncClient | None = None, cache_dir: Path | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=120.0, follow_redirects=True)
        self._cache_dir = cache_dir or Path.home() / ".cache" / "europagrad"

    async def load_country(self, iso2: str) -> list[Institution]:
        jsonl_path = await self._ensure_dump()
        cc = iso2.upper()
        out: list[Institution] = []
        for item in _iter_dump_items(jsonl_path):
            inst = parse_dump_item(item, cc)
            if inst:
                out.append(inst)
        out.sort(key=lambda i: i.name.lower())
        return out

    async def _ensure_dump(self) -> Path:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cached = self._latest_cached()
        if cached is not None:
            return cached
        record_id = await self._discover_latest_record()
        zip_path = await self._download(record_id)
        return self._extract_jsonl(zip_path)

    def _latest_cached(self) -> Path | None:
        candidates = sorted(self._cache_dir.glob("*ror-data*.json"))
        if not candidates:
            return None
        newest = candidates[-1]
        if time.time() - newest.stat().st_mtime > CACHE_TTL_S:
            return None
        return newest

    async def _discover_latest_record(self) -> int:
        resp = await self._client.get(
            ZENODO_SEARCH,
            params={"q": '"ROR Data"', "type": "dataset", "sort": "newest", "size": 5},
        )
        resp.raise_for_status()
        for hit in resp.json().get("hits", {}).get("hits", []):
            if (hit.get("metadata", {}).get("title") or "").strip() == "ROR Data":
                return int(hit["id"])
        raise RuntimeError("Could not discover latest ROR Data record on Zenodo")

    async def _download(self, record_id: int) -> Path:
        resp = await self._client.get(f"{ZENODO_SEARCH}/{record_id}")
        resp.raise_for_status()
        files = resp.json().get("files", [])
        if not files:
            raise RuntimeError(f"ROR record {record_id} has no files")
        file_meta = max(files, key=lambda f: f.get("size", 0))
        zip_path = self._cache_dir / file_meta["key"]
        if zip_path.exists() and time.time() - zip_path.stat().st_mtime <= CACHE_TTL_S:
            return zip_path
        download = await self._client.get(file_meta["links"]["self"])
        download.raise_for_status()
        zip_path.write_bytes(download.content)
        return zip_path

    @staticmethod
    def _extract_jsonl(zip_path: Path) -> Path:
        with zipfile.ZipFile(zip_path) as zf:
            jsonl_name = next(
                (n for n in zf.namelist() if n.endswith("ror-data.json") or n.endswith(".jsonl")),
                None,
            )
            if jsonl_name is None:
                raise RuntimeError(f"No ror-data JSON file inside {zip_path.name}")
            target = zip_path.with_suffix(".json")
            target.write_bytes(zf.read(jsonl_name))
            return target


def _iter_dump_items(path: Path):
    """Yield items from a ROR dump file: either a top-level JSON array (official
    dumps) or JSON-lines. Streams with bounded memory for the 300MB+ array form."""
    with path.open("r", encoding="utf-8") as fh:
        first = fh.read(1)
        if first != "[":
            fh.seek(0)
            for line in fh:
                line = line.strip().rstrip(",")
                if line and line not in ("[", "]"):
                    yield json.loads(line)
            return

        # Array form: skip the opening bracket, then stream items.
        fh.seek(1)
        decoder = json.JSONDecoder()
        buf = ""
        while True:
            chunk = fh.read(1 << 20)
            if chunk:
                buf += chunk
            pos = 0
            while True:
                while pos < len(buf) and buf[pos] in " \t\r\n,":
                    pos += 1
                if pos >= len(buf):
                    break
                if buf[pos] == "]":
                    return
                try:
                    item, end = decoder.raw_decode(buf, pos)
                except json.JSONDecodeError:
                    break
                yield item
                pos = end
            buf = buf[pos:]
            if not chunk:
                return


def parse_dump_item(item: dict, country_code: str) -> Institution | None:
    types = {t.lower() for t in item.get("types", [])}
    if "education" not in types:
        return None
    codes = {
        loc.get("geonames_details", {}).get("country_code", "")
        for loc in item.get("locations", [])
    }
    if country_code.upper() not in codes:
        return None

    display = None
    label = None
    for name in item.get("names", []):
        ntypes = set(name.get("types", []))
        if "ror_display" in ntypes:
            display = name.get("value")
        elif "label" in ntypes and label is None:
            label = name.get("value")
    name = display or label
    if not name:
        return None

    domains = item.get("domains") or []
    return Institution(
        name=name.strip(),
        country=country_code.upper(),
        domain=domains[0].lower() if domains else None,
        ror_id=item.get("id"),
        types=("education",),
    )
