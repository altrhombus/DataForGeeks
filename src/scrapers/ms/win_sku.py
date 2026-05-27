import re

from bs4 import BeautifulSoup

from src.models.ms.win_sku import WinSku
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getproductinfo"

# Each product type uses a definition-list structure inside a table cell:
#   <dt><b>PRODUCT_NAME</b></dt>  <dt>0xHEXVALUE</dt>  </dl></td>  <td ...>Description</td>
_ENTRY_RE = re.compile(
    r"<dt><b>(PRODUCT_[^<]+)</b></dt>\s*<dt>([^<]+)</dt>\s*</dl>\s*</td>\s*<td[^>]*>\s*(.*?)\s*</td>",
    re.IGNORECASE | re.DOTALL,
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


class WinSkuScraper(BaseScraper):
    dataset = "ms/win/sku"
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
            raise ValueError("No OS SKU entries parsed — page structure may have changed")

        seen: set[str] = set()
        unique: list[WinSku] = []
        for r in sorted(records, key=lambda x: x.dec):
            if r.value not in seen:
                seen.add(r.value)
                unique.append(r)

        return [r.model_dump() for r in unique]
