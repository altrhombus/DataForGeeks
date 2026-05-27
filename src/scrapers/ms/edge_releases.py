import re
from datetime import datetime as dt

from bs4 import BeautifulSoup

from src.models.ms.edge_release import EdgeRelease
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-stable-channel"
_ARCHIVE_URL = "https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnote-archive-stable-channel"

# "## Version 148.0.3967.54: May 07, 2026 (Stable)"
_VERSION_HEADING_RE = re.compile(
    r"Version\s+(\d+)\.(\d+)\.(\d+)\.(\d+)\s*:\s*([A-Za-z]+ \d{1,2},\s*\d{4})",
    re.IGNORECASE,
)


def _parse_edge_page(html: str) -> list[EdgeRelease]:
    soup = BeautifulSoup(html, "lxml")
    records: list[EdgeRelease] = []
    for el in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = el.get_text(strip=True)
        m = _VERSION_HEADING_RE.search(text)
        if not m:
            continue
        major = int(m.group(1))
        version = f"{m.group(1)}.{m.group(2)}.{m.group(3)}.{m.group(4)}"
        date_str = re.sub(r"\s+", " ", m.group(5)).strip()
        try:
            release_date = dt.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
        records.append(EdgeRelease(version=version, major_version=major, release_date=release_date))
    return records


class EdgeReleasesScraper(BaseScraper):
    dataset = "ms/other/edge-releases"
    dataset_name = "edge-releases"
    sources = [_SOURCE_URL, _ARCHIVE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[EdgeRelease] = []
        records.extend(_parse_edge_page(pages[_SOURCE_URL]))
        records.extend(_parse_edge_page(pages[_ARCHIVE_URL]))

        if not records:
            raise ValueError("No Edge release entries parsed — page structure may have changed")

        seen: set[tuple] = set()
        unique: list[EdgeRelease] = []
        for r in sorted(records, key=lambda x: (x.release_date, x.version)):
            key = (r.version, r.release_date)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return [r.model_dump() for r in unique]
