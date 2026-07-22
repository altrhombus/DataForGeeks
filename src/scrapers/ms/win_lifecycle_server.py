from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.win_lifecycle_server import WinLifecycleServer
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCES = [
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2008",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2008-r2",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2012",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2012-r2",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2016",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2019",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2022",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2025",
]


class WinLifecycleServerScraper(BaseScraper):
    """Scrapes Windows Server lifecycle dates from individual product pages on learn.microsoft.com.

    Each product page has two tables:
    - a "Listing" table with the product's overall start / mainstream end /
      extended end dates (one row, three <local-time> elements), and
    - a "Version | Start Date | End Date" releases table with per-tier rows
      (Service Packs, Extended Security Update years, Original Release —
      two <local-time> elements each).
    """

    dataset = "ms/win/lifecycle-server"
    dataset_name = "windows-lifecycle-server"
    sources = _SOURCES

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[WinLifecycleServer] = []

        for url in self.sources:
            soup = BeautifulSoup(pages[url], "lxml")

            h1 = soup.find("h1")
            version = h1.get_text(strip=True) if h1 else ""

            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                local_times = row.find_all("local-time")

                if len(cells) >= 4 and len(local_times) >= 3:
                    # Listing table: product row with all three lifecycle dates.
                    records.append(
                        WinLifecycleServer(
                            version=version,
                            tier=cells[0].get_text(strip=True),
                            start_date=_lt_date(local_times[0]),
                            mainstream_end_date=_lt_date(local_times[1]),
                            extended_end_date=_lt_date(local_times[2]),
                        )
                    )
                elif len(cells) == 3 and len(local_times) == 2:
                    # Releases table: tier row (SP / ESU year / Original Release)
                    # with only start and end dates. The end date is when all
                    # support for the tier stops, so it fills both end fields.
                    tier = cells[0].get_text(strip=True)
                    if not tier:
                        continue
                    end_date = _lt_date(local_times[1])
                    records.append(
                        WinLifecycleServer(
                            version=version,
                            tier=tier,
                            start_date=_lt_date(local_times[0]),
                            mainstream_end_date=end_date,
                            extended_end_date=end_date,
                        )
                    )

        if not records:
            raise StructureChangedError("No server lifecycle entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: (r.version, r.tier))
        return [r.model_dump() for r in unique]


def _lt_date(local_time) -> str:
    return str(local_time.get("datetime") or "")[:10]
