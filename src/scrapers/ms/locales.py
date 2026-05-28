from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.locale import Locale
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCE_URL = "https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/6c085406-a698-4e12-9d4d-c3b0ee3dbc4a"


class LocalesScraper(BaseScraper):
    """Scrapes Microsoft locale codes, hex values, and language tags from learn.microsoft.com."""

    dataset = "ms/other/locales"
    dataset_name = "locales"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")

        tables = soup.find_all("table")
        if not tables:
            raise StructureChangedError("No tables found — page structure may have changed")

        records: list[Locale] = []
        for row in tables[0].find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            lang_code_text = cells[0].get_text(strip=True)
            lang_name = cells[1].get_text(strip=True)
            lang_tag = cells[2].get_text(strip=True)

            if not lang_code_text or lang_code_text.lower().startswith("any"):
                continue

            try:
                lang_code = int(lang_code_text)
            except ValueError:
                continue

            records.append(
                Locale(
                    lang_code=lang_code,
                    lang_code_hex=f"{lang_code:04X}",
                    lang_name=lang_name,
                    lang_tag=lang_tag,
                )
            )

        if not records:
            raise StructureChangedError("No locale entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.lang_code)
        return [r.model_dump() for r in unique]
