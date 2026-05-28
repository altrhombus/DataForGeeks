import re

from src.exceptions import StructureChangedError
from src.models.ms.win_sku import WinSku
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCE_URL = "https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getproductinfo"

# Each product type uses a definition-list structure inside a table cell:
#   <dt><b>PRODUCT_NAME</b></dt>  <dt>0xHEXVALUE</dt>  </dl></td>  <td ...>Description</td>
_ENTRY_RE = re.compile(
    r"<dt><b>(PRODUCT_[^<]+)</b></dt>\s*<dt>([^<]+)</dt>\s*</dl>\s*</td>\s*<td[^>]*>\s*(.*?)\s*</td>",
    re.IGNORECASE | re.DOTALL,
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


class WinSkuScraper(BaseScraper):
    """Scrapes Windows product type (SKU) constants and their hex/decimal values from learn.microsoft.com."""

    dataset = "ms/win/sku"
    dataset_name = "windows-sku"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        html = pages[_SOURCE_URL]
        records: list[WinSku] = []

        for m in _ENTRY_RE.finditer(html):
            value = m.group(1).strip()
            hex_val = m.group(2).strip()
            meaning = _HTML_TAG_RE.sub("", m.group(3)).strip()

            try:
                dec = int(hex_val, 16)
            except ValueError:
                continue

            records.append(
                WinSku(
                    value=value,
                    hex=hex_val,
                    dec=dec,
                    meaning=meaning,
                )
            )

        if not records:
            raise StructureChangedError("No OS SKU entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.dec, key_fn=lambda r: r.value)
        return [r.model_dump() for r in unique]
