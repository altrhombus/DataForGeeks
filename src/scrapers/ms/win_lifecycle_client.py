from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.win_lifecycle_client import WinLifecycleClient
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCES = [
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-10-enterprise-and-education",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-11-enterprise-and-education",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-10-home-and-pro",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-11-home-and-pro",
]


class WinLifecycleClientScraper(BaseScraper):
    """Scrapes Windows 10/11 client lifecycle start and end dates from learn.microsoft.com."""

    dataset = "ms/win/lifecycle-client"
    dataset_name = "windows-lifecycle-client"
    sources = _SOURCES

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[WinLifecycleClient] = []

        for url in self.sources:
            soup = BeautifulSoup(pages[url], "lxml")

            h1 = soup.find("h1")
            sku = h1.get_text(strip=True) if h1 else ""

            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue

                version_text = cells[0].get_text(strip=True)
                if not version_text.startswith("Version "):
                    continue
                version = version_text.removeprefix("Version ").strip()

                local_times = row.find_all("local-time")
                if len(local_times) < 2:
                    continue

                start_date = str(local_times[0].get("datetime") or "")[:10]
                end_date = str(local_times[1].get("datetime") or "")[:10]

                records.append(
                    WinLifecycleClient(
                        version=version,
                        sku=sku,
                        start_date=start_date,
                        end_date=end_date,
                    )
                )

        if not records:
            raise StructureChangedError("No lifecycle entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.version, key_fn=lambda r: (r.version, r.sku))
        return [r.model_dump() for r in unique]
