import re

from src.models.ms.win_release import WinRelease
from src.scrapers.base import BaseScraper

_WIN10_URL = "https://learn.microsoft.com/en-us/windows/release-health/release-information"
_WIN11_URL = "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"

# Matches: <strong>Version 22H2 (OS Build 22621)</strong>
_VERSION_RE = re.compile(
    r"<strong>Version\s+(.*?)\s*\(OS [Bb]uild\s+(\d+)\)<\/strong>",
    re.IGNORECASE | re.DOTALL,
)


class WinReleasesScraper(BaseScraper):
    dataset = "ms/win/releases"
    sources = [_WIN10_URL, _WIN11_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[WinRelease] = []

        for url in self.sources:
            for m in _VERSION_RE.finditer(pages[url]):
                records.append(
                    WinRelease(
                        version=m.group(2),
                        full_version=f"10.0.{m.group(2)}",
                        build=m.group(1),
                    )
                )

        if not records:
            raise ValueError("No release entries parsed — page structure may have changed")

        seen: set[str] = set()
        unique: list[WinRelease] = []
        for r in sorted(records, key=lambda x: x.version):
            if r.version not in seen:
                seen.add(r.version)
                unique.append(r)

        return [r.model_dump() for r in unique]
