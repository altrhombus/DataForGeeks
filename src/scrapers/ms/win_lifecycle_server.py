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
    """Scrapes Windows Server lifecycle dates from individual product pages on learn.microsoft.com."""

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
                if len(cells) < 4:
                    continue

                tier = cells[0].get_text(strip=True)
                local_times = row.find_all("local-time")
                if len(local_times) < 3:
                    continue

                records.append(
                    WinLifecycleServer(
                        version=version,
                        tier=tier,
                        start_date=str(local_times[0].get("datetime") or "")[:10],
                        mainstream_end_date=str(local_times[1].get("datetime") or "")[:10],
                        extended_end_date=str(local_times[2].get("datetime") or "")[:10],
                    )
                )

        if not records:
            raise StructureChangedError("No server lifecycle entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: (r.version, r.tier))
        return [r.model_dump() for r in unique]
