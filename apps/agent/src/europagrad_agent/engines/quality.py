"""Page-quality heuristics: detect JS shells / empty pages that need escalation."""

from __future__ import annotations

from lxml import html as lxml_html

MIN_TEXT_CHARS = 200
MIN_TEXT_DENSITY = 0.02  # visible text bytes / raw html bytes


def assess(raw_html: str) -> tuple[int, float, bool]:
    """Return (text_chars, text_density, looks_like_js_shell).

    Handles HTML and plain text/markdown (Jina Reader output): if the content
    does not parse as HTML, it is treated as pure text with full density.
    """
    if not raw_html:
        return 0, 0.0, True
    try:
        doc = lxml_html.fromstring(raw_html)
    except Exception:
        chars = len(raw_html.strip())
        density = 1.0 if chars else 0.0
        return chars, density, chars < MIN_TEXT_CHARS

    for bad in doc.xpath("//script|//style|//noscript|//template"):
        bad.getparent().remove(bad)

    text = " ".join(t.strip() for t in doc.itertext() if t.strip())
    text_chars = len(text)
    density = text_chars / max(len(raw_html), 1)

    js_shell = (
        text_chars < MIN_TEXT_CHARS
        or density < MIN_TEXT_DENSITY
        or len(raw_html) < 1500
    ) and _has_spa_markers(raw_html)

    return text_chars, round(density, 4), js_shell


def _has_spa_markers(raw_html: str) -> bool:
    low = raw_html.lower()
    markers = (
        'id="root"',
        'id="app"',
        'id="__next"',
        'id="q-app"',
        "window.__initialstate__",
        "data-reactroot",
        "data-server-rendered",
        "<noscript>",
    )
    return any(m in low for m in markers)


def extract_links(raw_html: str, base_url: str) -> list[str]:
    try:
        doc = lxml_html.fromstring(raw_html)
    except Exception:
        return []
    out: list[str] = []
    for href in doc.xpath("//a/@href"):
        href = (href or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        out.append(_absolutize(href, base_url))
    return out


def _absolutize(href: str, base_url: str) -> str:
    from urllib.parse import urljoin, urlsplit

    if href.startswith("//"):
        scheme = urlsplit(base_url).scheme or "https"
        return f"{scheme}:{href}"
    return urljoin(base_url, href)
