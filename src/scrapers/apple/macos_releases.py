import logging
import re

from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.apple.macos_release import MacOsRelease
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted, parse_date

logger = logging.getLogger(__name__)

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
        name = cells[0].get_text(separator=" ", strip=True)   # col 0: OS name + version
        date_text = cells[2].get_text(strip=True)              # col 2: release date (col 1 is CVE links)
        m = _MACOS_RE.match(name)
        if not m:
            continue
        os_name = m.group(1)
        version = m.group(2)
        release_date = parse_date(date_text)
        if not release_date:
            logger.warning("Skipping row: could not parse date %r", date_text)
            continue
        major_version = int(version.partition(".")[0] or 0)
        records.append(MacOsRelease(
            os_name=os_name,
            version=version,
            major_version=major_version,
            release_date=release_date,
        ))
    return records


class MacOsReleasesScraper(BaseScraper):
    """Scrapes macOS release versions and dates from Apple's security releases page."""

    dataset = "apple/macos/releases"
    dataset_name = "macos-releases"
    sources = [_SOURCE_URL, _ARCHIVE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[MacOsRelease] = []
        records.extend(_parse_apple_page(pages[_SOURCE_URL]))
        records.extend(_parse_apple_page(pages[_ARCHIVE_URL]))

        if not records:
            raise StructureChangedError("No macOS release entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: (r.release_date, r.version), key_fn=lambda r: (r.version, r.release_date))
        return [r.model_dump() for r in unique]
