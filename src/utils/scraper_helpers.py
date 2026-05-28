"""Shared parsing utilities used across scraper implementations."""

from collections.abc import Callable, Generator, Hashable
from datetime import datetime as dt
from re import Pattern
from typing import Any

from bs4 import BeautifulSoup, Tag

# Common date formats used across Apple and Microsoft documentation pages
_DATE_FORMATS = ["%B %d, %Y", "%d %b %Y"]

_MS_SUPPORT_BASE = "https://support.microsoft.com"


def deduplicate_sorted[T](
    records: list[T],
    *,
    sort_key: Callable[[T], Any],
    key_fn: Callable[[T], Hashable] | None = None,
    reverse: bool = False,
) -> list[T]:
    """Sort *records* by *sort_key*, then return one record per unique *key_fn* value.

    The first occurrence in sorted order is kept when duplicates exist.
    When *key_fn* is omitted, *sort_key* doubles as the dedup key.
    """
    _key_fn = key_fn if key_fn is not None else sort_key
    seen: set[Hashable] = set()
    unique: list[T] = []
    for r in sorted(records, key=sort_key, reverse=reverse):
        k = _key_fn(r)
        if k not in seen:
            seen.add(k)
            unique.append(r)
    return unique


def parse_date(raw: str, *, formats: list[str] | None = None) -> str | None:
    """Parse *raw* into an ISO-8601 date string (YYYY-MM-DD).

    Tries each format in *formats* in order; uses the common Apple/MS formats
    when *formats* is omitted. Returns None on no match or empty input. Never raises.
    """
    raw = raw.strip()
    if not raw:
        return None
    for fmt in (formats or _DATE_FORMATS):
        try:
            return dt.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def iter_versioned_tables(
    soup: BeautifulSoup,
    version_re: Pattern[str],
    *,
    skip_unversioned: bool = True,
) -> Generator[tuple[str, Tag], None, None]:
    """Yield (version, table) pairs by tracking the version heading above each table.

    Scans h1–h4 and table elements in document order. When a heading matches
    *version_re*, its first capture group becomes the active version string. Each
    subsequent table element yields (version, table).

    If *skip_unversioned* is True (default), tables before the first matching
    heading are skipped.
    """
    current_version = ""
    for el in soup.find_all(["h1", "h2", "h3", "h4", "table"]):
        if el.name in ("h1", "h2", "h3", "h4"):
            m = version_re.search(el.get_text(strip=True))
            if m:
                current_version = m.group(1)
            continue
        if skip_unversioned and not current_version:
            continue
        yield current_version, el


def normalize_ms_url(href: str, base: str = _MS_SUPPORT_BASE) -> str | None:
    """Return an absolute URL for a Microsoft support link.

    *href* may be a full URL or a root-relative path starting with '/'.
    Returns None for empty or unrecognised input.
    """
    href = href.strip()
    if not href:
        return None
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base + href
    return None
