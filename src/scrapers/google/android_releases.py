import re
from datetime import datetime as dt

from bs4 import BeautifulSoup

from src.models.google.android_release import AndroidRelease
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://developer.android.com/tools/releases/platforms"

# "Android 16 (API level 36)" — single API level
_H2_SINGLE_RE = re.compile(r"Android\s+([\d.]+\w*)\s*\(API\s+level\s+(\d+)\)", re.IGNORECASE)
# "Android 12 (API levels 31, 32)" — multiple API levels
_H2_MULTI_RE = re.compile(r"Android\s+\d+\s*\(API\s+levels\s+([\d,\s]+)\)", re.IGNORECASE)
# "Revision 1 (June 2024)" or "Android 3.2, Revision 1 (July 2011)"
_H4_DATE_RE = re.compile(
    r"(?:Android\s+[\d.]+\w*,\s*)?Revision\s+(\d+)\s*\((\w+)\s+(\d{4})\)", re.IGNORECASE
)
# dt sub-entries for multi-API h2: "Android 12 (API level 31)"
_DT_SINGLE_RE = re.compile(r"Android\s+([\d.]+\w*)\s*\(API\s+level\s+(\d+)\)", re.IGNORECASE)
# dt sub-entries: "12L feature drop (API level 32)"
_DT_FEATURE_RE = re.compile(r"(\w+L)\s+feature\s+drop\s*\(API\s+level\s+(\d+)\)", re.IGNORECASE)


def _earliest_revision_date(h4_elements) -> str | None:
    best_rev = 9999
    best_date = None
    for h4 in h4_elements:
        m = _H4_DATE_RE.search(h4.get("data-text", ""))
        if not m:
            continue
        rev_num = int(m.group(1))
        if rev_num < best_rev:
            best_rev = rev_num
            try:
                best_date = dt.strptime(f"{m.group(2)} {m.group(3)}", "%B %Y").strftime("%Y-%m-01")
            except ValueError:
                pass
    return best_date


def _h4s_until_next_h2(h2):
    """Collect all h4.showalways elements in siblings after h2 until the next h2."""
    result = []
    for sib in h2.next_siblings:
        if getattr(sib, "name", None) == "h2":
            break
        if hasattr(sib, "find_all"):
            result.extend(sib.find_all("h4", class_="showalways"))
    return result


class AndroidReleasesScraper(BaseScraper):
    dataset = "google/android/releases"
    dataset_name = "android-releases"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")
        records: list[AndroidRelease] = []

        for h2 in soup.find_all("h2", {"data-text": True}):
            data_text = h2.get("data-text", "")

            # Single API level: "Android 15 (API level 35)"
            single_m = _H2_SINGLE_RE.match(data_text)
            if single_m:
                version = single_m.group(1)
                api_level = int(single_m.group(2))
                release_date = _earliest_revision_date(_h4s_until_next_h2(h2))
                if release_date:
                    records.append(AndroidRelease(
                        version=version, api_level=api_level, release_date=release_date
                    ))
                continue

            # Multiple API levels: "Android 12 (API levels 31, 32)"
            if _H2_MULTI_RE.match(data_text):
                dl = h2.find_next_sibling("dl")
                if not dl:
                    continue
                for dt_el in dl.find_all("dt"):
                    dt_text = dt_el.get_text(strip=True)
                    sm = _DT_SINGLE_RE.search(dt_text)
                    fm = _DT_FEATURE_RE.search(dt_text)
                    if sm:
                        version, api_level = sm.group(1), int(sm.group(2))
                    elif fm:
                        version, api_level = fm.group(1), int(fm.group(2))
                    else:
                        continue
                    dd = dt_el.find_next_sibling("dd")
                    if not dd:
                        continue
                    release_date = _earliest_revision_date(dd.find_all("h4", class_="showalways"))
                    if release_date:
                        records.append(AndroidRelease(
                            version=version, api_level=api_level, release_date=release_date
                        ))

        if not records:
            raise ValueError("No Android release entries parsed — page structure may have changed")

        return [r.model_dump() for r in sorted(records, key=lambda x: x.api_level, reverse=True)]
