import re
from datetime import datetime

from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.m365_build import M365Build
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCE_URL = "https://learn.microsoft.com/en-us/officeupdates/update-history-microsoft365-apps-by-date"

_VERSION_BUILD_RE = re.compile(r"Version\s+(\S+)\s+\(Build\s+([^)]+)\)", re.IGNORECASE)

# Header text → channel label. Column positions are derived from the header
# row at parse time so a column insertion or reorder cannot silently
# mislabel channels.
_CHANNEL_HEADERS = {
    "Current Channel": "Current",
    "Monthly Enterprise Channel": "Monthly Enterprise",
    "Semi-Annual Enterprise Channel (Preview)": "Semi-Annual Enterprise Preview",
    "Semi-Annual Enterprise Channel": "Semi-Annual Enterprise",
}


class M365BuildNumbersScraper(BaseScraper):
    """Scrapes Microsoft 365 Apps update history (build numbers by channel) from learn.microsoft.com."""

    dataset = "ms/apps/buildnumbers"
    dataset_name = "m365-update-history"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")

        history_table, columns = _find_history_table(soup)

        year_idx = columns["Year"]
        date_idx = columns["Release Date"]
        channel_cols = {
            idx: _CHANNEL_HEADERS[header]
            for header, idx in columns.items()
            if header in _CHANNEL_HEADERS
        }

        records: list[M365Build] = []
        last_year = ""

        for row in history_table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) <= max(channel_cols):
                continue

            year_text = cells[year_idx].get_text(strip=True)
            year = year_text if year_text else last_year
            last_year = year

            date_text = cells[date_idx].get_text(separator=" ", strip=True)
            # Remove any <br>-introduced whitespace artifacts
            date_text = re.sub(r"\s+", " ", date_text).strip()

            try:
                release_date = datetime.strptime(f"{date_text} {year}", "%B %d %Y").strftime("%Y-%m-%d")
            except ValueError:
                continue

            for col_idx, channel_name in channel_cols.items():
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
            raise StructureChangedError("No M365 release entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.release_date, key_fn=lambda r: (r.release_date, r.channel, r.build), reverse=True)
        return [r.model_dump() for r in unique]


def _find_history_table(soup) -> tuple:
    """Locate the release-history table by its header row and return it with a
    {header text: column index} map. Raises StructureChangedError when no table
    carries the expected Year / Release Date / channel headers."""
    for table in soup.find_all("table"):
        header_row = table.find("tr")
        if header_row is None:
            continue
        headers = [c.get_text(strip=True) for c in header_row.find_all(["th", "td"])]
        columns = {h: i for i, h in enumerate(headers)}
        if "Year" not in columns or "Release Date" not in columns:
            continue
        matched = [h for h in headers if h in _CHANNEL_HEADERS]
        if len(matched) != len(_CHANNEL_HEADERS):
            raise StructureChangedError(
                f"History table channel columns changed: expected {sorted(_CHANNEL_HEADERS)}, "
                f"found {matched} — page structure may have changed"
            )
        return table, columns
    raise StructureChangedError("Release-history table not found — page structure may have changed")
