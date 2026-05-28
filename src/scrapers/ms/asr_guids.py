import re

from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.asr_guid import AsrGuid
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted

_SOURCE_URL = "https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference"

_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


class AsrGuidsScraper(BaseScraper):
    """Scrapes Attack Surface Reduction rule names and GUIDs from learn.microsoft.com."""

    dataset = "ms/other/asr-guids"
    dataset_name = "asr-guids"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")

        # Each rule section uses an <h4> heading followed by a <ul> that
        # contains a <li> with <strong>GUID</strong>: <code>uuid</code>.
        records: list[AsrGuid] = []
        for h4 in soup.find_all("h4"):
            rule_name = h4.get_text(strip=True)

            ul = h4.find_next_sibling("ul")
            if ul is None:
                continue

            for li in ul.find_all("li", recursive=False):
                strong = li.find("strong")
                if strong and strong.get_text(strip=True) == "GUID":
                    code = li.find("code")
                    if code:
                        guid = code.get_text(strip=True).lower()
                        if _UUID_RE.fullmatch(guid):
                            records.append(AsrGuid(asr_name=rule_name, asr_guid=guid))
                    break

        if not records:
            raise StructureChangedError("No ASR GUID entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.asr_guid)
        return [r.model_dump() for r in unique]
