import re
from datetime import datetime as dt

from bs4 import BeautifulSoup

from src.models.apple.macos_release import MacOsRelease
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://support.apple.com/en-us/100100"
_ARCHIVE_URL = "https://support.apple.com/en-us/121012"

# "macOS Sequoia 15.7.7" or "macOS Tahoe 26"
_MACOS_RE = re.compile(r"^macOS\s+(\w+)\s+([\d.]+)", re.IGNORECASE)


def _parse_apple_page(html: str) -> list[MacOsRelease]:
    soup = BeautifulSoup(html, "lxml")
    records: list[MacOsRelease] = []
    for row in soup.select("table tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        name = cells[0].get_text(separator=" ", strip=True)
        date_text = cells[2].get_text(strip=True)
        m = _MACOS_RE.match(name)
        if not m:
            continue
        os_name = m.group(1)
        version = m.group(2)
        try:
            release_date = dt.strptime(date_text, "%d %b %Y").strftime("%Y-%m-%d")
        except ValueError:
            try:
                release_date = dt.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")
            except ValueError:
                continue
        major_version = int(version.split(".")[0])
        records.append(MacOsRelease(
            os_name=os_name,
            version=version,
            major_version=major_version,
            release_date=release_date,
        ))
    return records


class MacOsReleasesScraper(BaseScraper):
    dataset = "apple/macos/releases"
    dataset_name = "macos-releases"
    sources = [_SOURCE_URL, _ARCHIVE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[MacOsRelease] = []
        records.extend(_parse_apple_page(pages[_SOURCE_URL]))
        records.extend(_parse_apple_page(pages[_ARCHIVE_URL]))

        if not records:
            raise ValueError("No macOS release entries parsed — page structure may have changed")

        seen: set[tuple] = set()
        unique: list[MacOsRelease] = []
        for r in sorted(records, key=lambda x: (x.release_date, x.version)):
            key = (r.version, r.release_date)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return [r.model_dump() for r in unique]
