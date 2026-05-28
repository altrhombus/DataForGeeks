import re

from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.chassis_type import ChassisType
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCE_URL = "https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/cim-chassis"

# Matches " (42)" following a <strong> element
_NUMBER_RE = re.compile(r"\((\d+)\)")


class ChassisTypesScraper(BaseScraper):
    """Scrapes CIM chassis type names and numeric codes from learn.microsoft.com."""

    dataset = "ms/other/chassis-types"
    dataset_name = "chassis-types"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")

        # ChassisTypes entries appear before CreationClassName alphabetically.
        # Stop iteration when we hit that <strong> to avoid false matches.
        boundary = next(
            (s for s in soup.find_all("strong") if s.get_text(strip=True) == "CreationClassName"),
            None,
        )
        if boundary is None:
            raise StructureChangedError(
                "CreationClassName section boundary not found — page structure may have changed"
            )

        records: list[ChassisType] = []
        for strong in soup.find_all("strong"):
            if strong is boundary:
                break
            sibling = strong.next_sibling
            if not sibling:
                continue
            m = _NUMBER_RE.search(str(sibling))
            if m:
                records.append(
                    ChassisType(value=strong.get_text(strip=True), number=int(m.group(1)))
                )

        if not records:
            raise StructureChangedError(
                "No chassis type entries parsed — page structure may have changed"
            )

        unique = deduplicate_sorted(records, sort_key=lambda r: r.number)
        return [r.model_dump() for r in unique]
