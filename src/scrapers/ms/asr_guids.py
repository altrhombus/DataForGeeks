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
        # The GUID <ul> is not always the first list in the section — some
        # rules (e.g. "Use advanced protection against ransomware") have a
        # descriptive bullet list first — so scan every <ul> sibling up to
        # the next heading.
        records: list[AsrGuid] = []
        for h4 in soup.find_all("h4"):
            rule_name = h4.get_text(strip=True)

            guid = _find_section_guid(h4)
            if guid:
                records.append(AsrGuid(asr_name=rule_name, asr_guid=guid))

        if not records:
            raise StructureChangedError("No ASR GUID entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: r.asr_guid)
        return [r.model_dump() for r in unique]


def _find_section_guid(heading) -> str | None:
    """Return the GUID from the first <strong>GUID</strong> list item between
    *heading* and the next heading, or None if the section has no GUID."""
    sib = heading.find_next_sibling()
    while sib is not None and sib.name not in ("h2", "h3", "h4"):
        if sib.name == "ul":
            for li in sib.find_all("li", recursive=False):
                strong = li.find("strong")
                if strong and strong.get_text(strip=True) == "GUID":
                    code = li.find("code")
                    if code:
                        guid = code.get_text(strip=True).lower()
                        if _UUID_RE.fullmatch(guid):
                            return guid
                    return None
        sib = sib.find_next_sibling()
    return None
