from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.win_lifecycle_ltsc import WinLifecycleLtsc
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCE_URL = "https://learn.microsoft.com/en-us/windows/release-health/release-information"


class WinLifecycleLtscScraper(BaseScraper):
    """Scrapes Windows LTSC build and lifecycle data from the release health page on learn.microsoft.com."""

    dataset = "ms/win/lifecycle-ltsc"
    dataset_name = "windows-lifecycle-ltsc"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")

        # Find the table that contains "Long-Term Servicing" text
        ltsc_table = None
        for table in soup.find_all("table"):
            if "Long-Term Servicing" in table.get_text():
                ltsc_table = table
                break

        if ltsc_table is None:
            raise StructureChangedError("LTSC summary table not found — page structure may have changed")

        records: list[WinLifecycleLtsc] = []
        for row in ltsc_table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) != 8:
                continue

            # Table columns: Version | Servicing Option | Start | Mainstream End |
            #   Extended End | (unused) | (unused) | Latest Build
            version = cells[0].get_text(strip=True)
            if not version or version.lower() == "version":
                continue

            servicing_option = cells[1].get_text(strip=True)
            start_date = cells[2].get_text(strip=True)
            mainstream_end = cells[3].get_text(strip=True)
            # col 4 may have trailing text after the date; take the first token
            extended_raw = cells[4].get_text(strip=True)
            extended_end = extended_raw.split()[0] if extended_raw else ""
            # col 7: latest build as "NNNNN.XXXX"; keep only the base build (before the dot)
            latest_build_text = cells[7].get_text(strip=True)
            build = latest_build_text.partition(".")[0] if latest_build_text else ""

            records.append(
                WinLifecycleLtsc(
                    version=version,
                    servicing_option=servicing_option,
                    build=build,
                    start_date=start_date,
                    mainstream_end_date=mainstream_end,
                    extended_end_date=extended_end,
                )
            )

        if not records:
            raise StructureChangedError("No LTSC entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.version)
        return [r.model_dump() for r in unique]
