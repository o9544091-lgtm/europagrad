"""Sitemap keyword harvester (task 8).

Per university domain: discover sitemaps via robots.txt `Sitemap:` directives
plus conventional paths (domain and www variant, .xml and .xml.gz), expand
<sitemapindex> one level, keyword-filter URLs, cap per-domain candidates.
robots.txt respected via the shared politeness layer.
"""

from __future__ import annotations

import gzip
import zlib
from dataclasses import dataclass, field

import httpx
from lxml import etree

from europagrad_agent.engines.politeness import USER_AGENT, DomainThrottle, RobotCache

DEFAULT_KEYWORDS = (
    "master", "masters", "msc", "ma-", "/ma/", "admission", "international",
    "tuition", "fee", "scholarship", "english", "moi", "requirement",
    "prospective", "study", "programme", "program",
)
NON_CONTENT_MARKERS = (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".xml?", "wp-login", "/feed", ".css", ".js")


@dataclass
class HarvestResult:
    domain: str
    sitemap_found: bool = False
    candidates: list[str] = field(default_factory=list)
    total_urls_seen: int = 0


class SitemapHarvester:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        robots: RobotCache | None = None,
        throttle: DomainThrottle | None = None,
        keywords: tuple[str, ...] = DEFAULT_KEYWORDS,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=20.0
        )
        self._robots = robots or RobotCache(self._client)
        self._throttle = throttle or DomainThrottle()
        self._keywords = tuple(k.lower() for k in keywords)

    async def harvest(self, domain: str, cap: int = 40) -> HarvestResult:
        result = HarvestResult(domain=domain)
        base = f"https://{domain}"

        if not await self._robots.allowed(f"{base}/"):
            return result

        candidate_maps = await self._robots.declared_sitemaps(f"{base}/")
        conventional = [f"{base}/sitemap.xml", f"{base}/sitemap.xml.gz"]
        if not domain.startswith("www."):
            conventional += [f"https://www.{domain}/sitemap.xml", f"https://www.{domain}/sitemap.xml.gz"]
        for url in conventional:
            if url not in candidate_maps:
                candidate_maps.append(url)

        for sitemap_url in candidate_maps:
            if len(result.candidates) >= cap:
                break
            if not await self._robots.allowed(sitemap_url):
                continue
            await self._throttle.wait(domain)
            child_maps = await self._fetch_sitemap_list(sitemap_url)
            if child_maps is None:
                continue
            result.sitemap_found = True
            for child in child_maps:
                if len(result.candidates) >= cap:
                    break
                if not await self._robots.allowed(child):
                    continue
                await self._throttle.wait(domain)
                for url in await self._fetch_urlset(child):
                    result.total_urls_seen += 1
                    if len(result.candidates) >= cap:
                        break
                    if self._is_candidate(url):
                        result.candidates.append(url)
            if result.candidates:
                break
        return result

    def _is_candidate(self, url: str) -> bool:
        low = url.lower()
        if any(marker in low for marker in NON_CONTENT_MARKERS):
            return False
        return any(k in low for k in self._keywords)

    @staticmethod
    def _decode(resp: httpx.Response) -> bytes:
        content = resp.content
        if resp.url.path.endswith(".gz") or content[:2] == b"\x1f\x8b":
            try:
                content = gzip.decompress(content)
            except (gzip.BadGzipFile, zlib.error):
                return b""
        return content

    async def _fetch_sitemap_list(self, sitemap_url: str) -> list[str] | None:
        """Returns child sitemap URLs for an index, [url] for a plain urlset, None if 404/invalid."""
        try:
            resp = await self._client.get(sitemap_url)
        except httpx.HTTPError:
            return None
        if resp.status_code == 404:
            return None
        if resp.status_code >= 400:
            return None
        try:
            root = etree.fromstring(self._decode(resp))
        except etree.XMLSyntaxError:
            return None
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        index_entries = root.xpath("//sm:sitemap/sm:loc/text()", namespaces=ns)
        if index_entries:
            return [str(u) for u in index_entries]
        urlset = root.xpath("//sm:url/sm:loc/text()", namespaces=ns)
        if urlset:
            return [sitemap_url]
        # sitemap without namespace
        plain = root.xpath("//*[local-name()='url']/*[local-name()='loc']/text()")
        if plain:
            return [sitemap_url]
        return []

    async def _fetch_urlset(self, sitemap_url: str) -> list[str]:
        try:
            resp = await self._client.get(sitemap_url)
        except httpx.HTTPError:
            return []
        if resp.status_code >= 400:
            return []
        try:
            root = etree.fromstring(self._decode(resp))
        except etree.XMLSyntaxError:
            return []
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = root.xpath("//sm:url/sm:loc/text()", namespaces=ns)
        if not locs:
            locs = root.xpath("//*[local-name()='url']/*[local-name()='loc']/text()")
        return [str(u) for u in locs]
