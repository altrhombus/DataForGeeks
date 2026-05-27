from bs4 import BeautifulSoup

from src.models.ms.win_lifecycle_server import WinLifecycleServer
from src.scrapers.base import BaseScraper

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
                        start_date=local_times[0].get("datetime", "")[:10],
                        mainstream_end_date=local_times[1].get("datetime", "")[:10],
                        extended_end_date=local_times[2].get("datetime", "")[:10],
                    )
                )

        if not records:
            raise ValueError("No server lifecycle entries parsed — page structure may have changed")

        seen: set[tuple] = set()
        unique: list[WinLifecycleServer] = []
        for r in sorted(records, key=lambda x: (x.version, x.tier)):
            key = (r.version, r.tier)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return [r.model_dump() for r in unique]
