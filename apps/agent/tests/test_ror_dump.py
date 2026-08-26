"""Tests for the ROR dump loader (task 8). Hermetic: fake zip + mocked Zenodo."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest

from europagrad_agent.registries.ror_dump import RorDumpLoader, parse_dump_item


def dump_item(name: str, cc: str, ror_id: str, domain: str | None, types: list[str]) -> dict:
    item = {
        "id": ror_id,
        "types": types,
        "names": [
            {"lang": "en", "types": ["ror_display", "label"], "value": name},
            {"lang": None, "types": ["acronym"], "value": name[:4].upper()},
        ],
        "locations": [
            {"geonames_details": {"country_code": cc, "country_name": "X", "name": "City"}}
        ],
    }
    if domain:
        item["domains"] = [domain]
    return item


class TestParseDumpItem:
    def test_education_in_country_parsed(self) -> None:
        inst = parse_dump_item(dump_item("University of Tartu", "EE", "https://ror.org/a", "ut.ee", ["education", "funder"]), "EE")
        assert inst is not None
        assert inst.name == "University of Tartu"
        assert inst.domain == "ut.ee"
        assert inst.ror_id == "https://ror.org/a"

    def test_non_education_rejected(self) -> None:
        assert parse_dump_item(dump_item("ACME", "EE", "https://ror.org/x", "acme.io", ["company"]), "EE") is None

    def test_wrong_country_rejected(self) -> None:
        assert parse_dump_item(dump_item("Uni X", "LV", "https://ror.org/y", "x.lv", ["education"]), "EE") is None

    def test_label_fallback_when_no_display(self) -> None:
        item = dump_item("ignored", "EE", "https://ror.org/z", None, ["education"])
        item["names"] = [{"lang": "en", "types": ["label"], "value": "Fallback University"}]
        inst = parse_dump_item(item, "EE")
        assert inst is not None
        assert inst.name == "Fallback University"
        assert inst.domain is None


def make_fake_dump(tmp_path: Path, items: list[dict], array_form: bool = True) -> Path:
    zip_path = tmp_path / "vX-ror-data.zip"
    content = json.dumps(items, indent=2) if array_form else "\n".join(json.dumps(i) for i in items)
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("vX-ror-data.json", content)
    return zip_path


class TestDumpLoader:
    async def test_load_country_from_cached_array_dump(self, tmp_path: Path) -> None:
        """Official dumps are a top-level JSON array — must stream correctly."""
        make_fake_dump(
            tmp_path,
            [
                dump_item("Uni A", "EE", "https://ror.org/a", "a.edu", ["education"]),
                dump_item("Uni B", "EE", "https://ror.org/b", None, ["education"]),
                dump_item("Uni LV", "LV", "https://ror.org/c", "c.lv", ["education"]),
                dump_item("Corp D", "EE", "https://ror.org/d", "d.io", ["company"]),
            ],
            array_form=True,
        )
        jsonl = tmp_path / "vX-ror-data.json"
        with zipfile.ZipFile(tmp_path / "vX-ror-data.zip") as zf:
            jsonl.write_bytes(zf.read("vX-ror-data.json"))

        class FakeClient:
            def __getattr__(self, name):  # pragma: no cover - guard
                raise AssertionError("network should not be used when cache exists")

        loader = RorDumpLoader(client=FakeClient(), cache_dir=tmp_path)
        institutions = await loader.load_country("EE")
        assert {i.name for i in institutions} == {"Uni A", "Uni B"}

    async def test_load_country_from_cached_jsonl_dump(self, tmp_path: Path) -> None:
        make_fake_dump(
            tmp_path,
            [
                dump_item("Uni A", "EE", "https://ror.org/a", "a.edu", ["education"]),
                dump_item("Uni B", "EE", "https://ror.org/b", None, ["education"]),
                dump_item("Uni LV", "LV", "https://ror.org/c", "c.lv", ["education"]),
                dump_item("Corp D", "EE", "https://ror.org/d", "d.io", ["company"]),
            ],
            array_form=False,
        )
        jsonl = tmp_path / "vX-ror-data.json"
        with zipfile.ZipFile(tmp_path / "vX-ror-data.zip") as zf:
            jsonl.write_bytes(zf.read("vX-ror-data.json"))

        class FakeClient:
            def __getattr__(self, name):  # pragma: no cover - guard
                raise AssertionError("network should not be used when cache exists")

        loader = RorDumpLoader(client=FakeClient(), cache_dir=tmp_path)
        institutions = await loader.load_country("EE")
        assert {i.name for i in institutions} == {"Uni A", "Uni B"}

    async def test_discover_picks_exact_title(self, tmp_path: Path) -> None:
        search_payload = {
            "hits": {
                "hits": [
                    {"id": 111, "metadata": {"title": "ROR Data Extra"}},
                    {"id": 222, "metadata": {"title": "ROR Data"}},
                ]
            }
        }
        record_payload = {
            "files": [
                {"key": "v1-ror-data.zip", "size": 10, "links": {"self": "https://zenodo.org/api/records/222/files/v1-ror-data.zip/content"}}
            ]
        }
        zip_bytes = b""

        def handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if url.startswith("https://zenodo.org/api/records?"):
                return httpx.Response(200, json=search_payload)
            if "records/222" in url and "files" not in url:
                return httpx.Response(200, json=record_payload)
            if "files/v1-ror-data.zip/content" in url:
                nonlocal zip_bytes
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w") as zf:
                    zf.writestr("v1-ror-data.json", json.dumps(dump_item("Uni Z", "EE", "https://ror.org/z", "z.edu", ["education"])))
                zip_bytes = buf.getvalue()
                return httpx.Response(200, content=zip_bytes)
            return httpx.Response(404)

        loader = RorDumpLoader(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), cache_dir=tmp_path)
        institutions = await loader.load_country("EE")
        assert [i.name for i in institutions] == ["Uni Z"]

    async def test_discover_failure_raises_clean_error(self, tmp_path: Path) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"hits": {"hits": [{"id": 1, "metadata": {"title": "Something Else"}}]}})

        loader = RorDumpLoader(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), cache_dir=tmp_path)
        with pytest.raises(RuntimeError, match="Could not discover"):
            await loader.load_country("EE")
