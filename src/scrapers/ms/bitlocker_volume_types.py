import re

from src.models.ms.bitlocker_volume_type import BitlockerVolumeType
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://learn.microsoft.com/en-us/graph/api/resources/bitlockerrecoverykey?view=graph-rest-1.0"

# The volumeType enum is described inline as: <code>1</code> (for <code>operatingSystemVolume</code>)
_ENTRY_RE = re.compile(r"<code>(\d+)</code>\s*\(for\s*<code>([^<]+)</code>\)")


class BitlockerVolumeTypesScraper(BaseScraper):
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
            raise ValueError("No volumeType enum entries parsed — page structure may have changed")

        seen: set[int] = set()
        unique: list[BitlockerVolumeType] = []
        for r in sorted(records, key=lambda x: x.volume_type_enum):
            if r.volume_type_enum not in seen:
                seen.add(r.volume_type_enum)
                unique.append(r)

        return [r.model_dump() for r in unique]
