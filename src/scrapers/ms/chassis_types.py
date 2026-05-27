import re

from src.models.ms.chassis_type import ChassisType
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/cim-chassis"

# ChassisTypes entries appear as: <strong>Name</strong> (Number)
_ENTRY_RE = re.compile(r"<strong>([^<]+)</strong>\s*\((\d+)\)")


class ChassisTypesScraper(BaseScraper):
    dataset = "ms/other/chassis-types"
    dataset_name = "chassis-types"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        html = pages[_SOURCE_URL]

        # The ChassisTypes section precedes CreationClassName alphabetically.
        # Split on the CreationClassName heading to avoid false matches.
        boundary = "<strong>CreationClassName</strong>"
        if boundary not in html:
            raise ValueError("CreationClassName section boundary not found — page structure may have changed")
        chassis_section = html.split(boundary)[0]

        records: list[ChassisType] = []
        for m in _ENTRY_RE.finditer(chassis_section):
            value = m.group(1).strip()
            number = int(m.group(2))
            records.append(ChassisType(value=value, number=number))

        if not records:
            raise ValueError("No chassis type entries parsed — page structure may have changed")

        seen: set[int] = set()
        unique: list[ChassisType] = []
        for r in sorted(records, key=lambda x: x.number):
            if r.number not in seen:
                seen.add(r.number)
                unique.append(r)

        return [r.model_dump() for r in unique]
