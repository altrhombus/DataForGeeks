import re

from src.exceptions import StructureChangedError
from src.models.ms.win_release import WinRelease
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_WIN10_URL = "https://learn.microsoft.com/en-us/windows/release-health/release-information"
_WIN11_URL = "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"

# Matches: <strong>Version 22H2 (OS Build 22621)</strong>
_VERSION_RE = re.compile(
    r"<strong>Version\s+(.*?)\s*\(OS [Bb]uild\s+(\d+)\)<\/strong>",
    re.IGNORECASE | re.DOTALL,
)


class WinReleasesScraper(BaseScraper):
    """Scrapes Windows 10/11 release version-to-build mappings from learn.microsoft.com."""

    dataset = "ms/win/releases"
    dataset_name = "windows-release-history"
    sources = [_WIN10_URL, _WIN11_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[WinRelease] = []

        for url, major_version in zip(self.sources, [10, 11], strict=True):
            for m in _VERSION_RE.finditer(pages[url]):
                records.append(
                    WinRelease(
                        os_type="client",
                        major_version=major_version,
                        windows_version=m.group(1),
                        os_build=m.group(2),
                        full_version=f"10.0.{m.group(2)}",
                    )
                )

        if not records:
            raise StructureChangedError("No release entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.os_build)
        return [r.model_dump() for r in unique]
