import re
from datetime import datetime

from bs4 import BeautifulSoup

from src.models.ms.m365_build import M365Build
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://learn.microsoft.com/en-us/officeupdates/update-history-microsoft365-apps-by-date"

_VERSION_BUILD_RE = re.compile(r"Version\s+(\S+)\s+\(Build\s+([^)]+)\)", re.IGNORECASE)

_CHANNELS = {
    2: "Current",
    3: "Monthly Enterprise",
    4: "Semi-Annual Enterprise Preview",
    5: "Semi-Annual Enterprise",
}


class M365BuildNumbersScraper(BaseScraper):
    dataset = "ms/apps/buildnumbers"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")

        tables = soup.find_all("table")
        if len(tables) < 2:
            raise ValueError(
                f"Expected at least 2 tables, found {len(tables)} — page structure may have changed"
            )

        # Table at index 1: Year | Date | Current | Monthly Enterprise | SAEP | SAE
        records: list[M365Build] = []
        last_year = ""

        for row in tables[1].find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 6:
                continue

            year_text = cells[0].get_text(strip=True)
            year = year_text if year_text else last_year
            last_year = year

            date_text = cells[1].get_text(separator=" ", strip=True)
            # Remove any <br>-introduced whitespace artifacts
            date_text = re.sub(r"\s+", " ", date_text).strip()

            try:
                release_date = datetime.strptime(f"{date_text} {year}", "%B %d %Y").strftime("%Y-%m-%d")
            except ValueError:
                continue

            for col_idx, channel_name in _CHANNELS.items():
                cell_text = cells[col_idx].get_text(separator=" ", strip=True)
                for m in _VERSION_BUILD_RE.finditer(cell_text):
                    version = m.group(1).strip()
                    build = m.group(2).strip()
                    records.append(
                        M365Build(
                            release_date=release_date,
                            channel=channel_name,
                            build=build,
                            version=version,
                            full_build=f"16.0.{build}",
                        )
                    )

        if not records:
            raise ValueError("No M365 release entries parsed — page structure may have changed")

        seen: set[tuple] = set()
        unique: list[M365Build] = []
        for r in sorted(records, key=lambda x: x.release_date, reverse=True):
            key = (r.release_date, r.channel, r.build)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return [r.model_dump() for r in unique]
