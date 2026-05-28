import re

from src.exceptions import StructureChangedError
from src.models.ms.bitlocker_volume_type import BitlockerVolumeType
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCE_URL = "https://learn.microsoft.com/en-us/graph/api/resources/bitlockerrecoverykey?view=graph-rest-1.0"

# The volumeType enum is described inline as: <code>1</code> (for <code>operatingSystemVolume</code>)
_ENTRY_RE = re.compile(r"<code>(\d+)</code>\s*\(for\s*<code>([^<]+)</code>\)")


class BitlockerVolumeTypesScraper(BaseScraper):
    """Scrapes BitLocker volumeType enum values from the Microsoft Graph API reference."""

    dataset = "ms/other/bitlocker-volume-types"
    dataset_name = "bitlocker-volume-types"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[BitlockerVolumeType] = []

        for m in _ENTRY_RE.finditer(pages[_SOURCE_URL]):
            records.append(
                BitlockerVolumeType(
                    volume_type_enum=int(m.group(1)),
                    description=m.group(2).strip(),
                )
            )

        if not records:
            raise StructureChangedError("No volumeType enum entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.volume_type_enum)
        return [r.model_dump() for r in unique]
