import logging
import re
from datetime import datetime as dt

from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.dotnet_lifecycle import DotnetLifecycle
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

logger = logging.getLogger(__name__)

_FRAMEWORK_URL = "https://learn.microsoft.com/en-us/lifecycle/products/microsoft-net-framework"
_DOTNET_URL = "https://learn.microsoft.com/en-us/lifecycle/products/microsoft-net-and-net-core"

# ISO 8601 timestamp with optional timezone: 2022-08-09T00:00:00.000-08:00
_ISO_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})(?:T[\d:.+-]+)?")


def _parse_date(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    m = _ISO_DATE_RE.match(raw)
    if m:
        return m.group(1)
    # Fallback: "Month DD, YYYY"
    try:
        return dt.strptime(raw, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _parse_lifecycle_page(html: str, product_label: str) -> list[DotnetLifecycle]:
    soup = BeautifulSoup(html, "lxml")
    records: list[DotnetLifecycle] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        header = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        # Expect a version column and at least one date column
        if not any("version" in h for h in header):
            continue
        if not any("date" in h or "start" in h for h in header):
            continue

        # Find column indices
        version_idx = next((i for i, h in enumerate(header) if "version" in h), None)
        start_idx = next((i for i, h in enumerate(header) if "start" in h or ("date" in h and "end" not in h)), None)
        end_idx = next((i for i, h in enumerate(header) if "end" in h or "retire" in h), None)

        if version_idx is None or start_idx is None:
            continue

        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) <= max(filter(None, [version_idx, start_idx, end_idx or 0])):
                continue

            version_raw = cells[version_idx].get_text(strip=True)
            if not version_raw:
                continue

            # Strip product prefix to get just the version number
            version = re.sub(r"(?i)\.net\s+(framework\s+)?", "", version_raw).strip()
            if not version:
                continue

            start_raw = cells[start_idx].get_text(strip=True) if start_idx < len(cells) else ""
            end_raw = cells[end_idx].get_text(strip=True) if end_idx is not None and end_idx < len(cells) else ""

            release_date = _parse_date(start_raw)
            if not release_date:
                logger.warning("Skipping row: could not parse date %r", start_raw)
                continue

            end_date = _parse_date(end_raw)

            records.append(
                DotnetLifecycle(
                    product=product_label,
                    version=version,
                    release_date=release_date,
                    end_date=end_date,
                )
            )

    return records


class DotnetLifecycleScraper(BaseScraper):
    """Scrapes .NET and .NET Framework lifecycle dates from learn.microsoft.com."""

    dataset = "ms/other/dotnet-lifecycle"
    dataset_name = "dotnet-lifecycle"
    sources = [_FRAMEWORK_URL, _DOTNET_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[DotnetLifecycle] = []
        records.extend(_parse_lifecycle_page(pages[_FRAMEWORK_URL], ".NET Framework"))
        records.extend(_parse_lifecycle_page(pages[_DOTNET_URL], ".NET"))

        if not records:
            raise StructureChangedError("No .NET lifecycle entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: (r.product, r.version))
        return [r.model_dump() for r in unique]
