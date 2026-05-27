import re
from datetime import date
from html import unescape

from bs4 import BeautifulSoup

from src.models.ms.win_buildnumber import WinBuildNumber
from src.scrapers.base import BaseScraper

_WIN10_URL = "https://support.microsoft.com/en-us/topic/windows-10-update-history-24ea91f4-36e7-d8fd-0ddb-d79d9d0cdbda"
_WIN11_URL = "https://aka.ms/Windows11UpdateHistory"
_SERVER2022_URL = "https://support.microsoft.com/en-us/topic/windows-server-2022-update-history-e1caa597-00c5-4ab9-9f3e-8212fe80b2ee"
_HOTPATCH_URL = "https://support.microsoft.com/en-us/topic/release-notes-for-hotpatch-on-windows-11-enterprise-version-25h2-0bbaa1c7-5070-41ca-a7c9-4ead79602dbf"

# Matches link text like: "May 13, 2026—KB5058411 (OS Build 22621.5192)"
# Group 1: description ("May 13, 2026—KB5058411")
# Group 2: one or more build numbers ("22621.5192" or "22621.5192 and 22621.5193")
# Group 3: trailing comment (usually empty)
_OS_BUILD_RE = re.compile(
    r"(.+?)\s*\(OS Builds?\s+([\d.,\s]+(?:\s+and\s+[\d.,\s]+)?)\)(.*)",
    re.IGNORECASE,
)

# Matches "May 13, 2026—KB5058411" (em-dash or regular dash)
_PATCH_DESC_RE = re.compile(
    r"^(.*?\d{1,2}[,]\s*\d{4})\s*[—\-–]+\s*(KB\d+)",
    re.IGNORECASE,
)

# Matches the hotpatch article URL slug to extract date + build numbers
# e.g. "january-14-2025-hotpatch-kb5051978-os-builds-26100-2605-and-26100-2606"
_HOTPATCH_HREF_RE = re.compile(
    r"(\w+)-(\d{1,2})-(\d{4})-hotpatch.*?os-builds?-(\d+)-(\d+)-and-(\d+)-(\d+)",
    re.IGNORECASE,
)
_KB_RE = re.compile(r"KB\d+", re.IGNORECASE)

# Manually verified: this build was released for Windows Server only
_SERVER_ONLY_BUILDS = {"10.0.14393.5127"}

# 17763.* builds released on or after this date are LTSC-only
_LTSC_CUTOFF = date(2021, 5, 12)


class WinBuildNumbersScraper(BaseScraper):
    dataset = "ms/win/buildnumbers"
    sources = [_WIN10_URL, _WIN11_URL, _SERVER2022_URL, _HOTPATCH_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[WinBuildNumber] = []

        for url in (_WIN10_URL, _WIN11_URL, _SERVER2022_URL):
            records.extend(_parse_standard_page(pages[url]))

        records.extend(_parse_hotpatch_page(pages[_HOTPATCH_URL]))

        if not records:
            raise ValueError("No build entries parsed — page structure may have changed")

        # Deduplicate then sort
        seen: set[tuple] = set()
        unique: list[WinBuildNumber] = []
        for r in sorted(records, key=lambda x: (x.release_date, x.build)):
            key = (r.full_version, r.release_date, r.kb_article)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        # Manual overrides
        unique = [r for r in unique if r.full_version not in _SERVER_ONLY_BUILDS]
        for r in unique:
            if r.full_version.startswith("10.0.17763."):
                if date.fromisoformat(r.release_date) >= _LTSC_CUTOFF:
                    object.__setattr__(r, "ltsc_only", True)  # pydantic model

        return [r.model_dump() for r in unique]


def _parse_standard_page(html: str) -> list[WinBuildNumber]:
    soup = BeautifulSoup(html, "lxml")
    records: list[WinBuildNumber] = []

    for a in soup.find_all("a"):
        text = unescape(a.get_text(strip=True))
        m = _OS_BUILD_RE.match(text)
        if not m:
            continue

        description = m.group(1).strip()
        versions_raw = m.group(2)
        comment = m.group(3).strip()

        pd = _PATCH_DESC_RE.match(description)
        if not pd:
            continue

        try:
            from datetime import datetime
            release_date = datetime.strptime(pd.group(1).strip(), "%B %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            continue

        kb_article = pd.group(2).upper()

        versions = [
            v.strip()
            for v in re.split(r"\s+and\s+|,", versions_raw)
            if v.strip()
        ]

        for version in versions:
            records.append(
                WinBuildNumber(
                    full_version=f"10.0.{version}",
                    build=version,
                    release_date=release_date,
                    kb_article=kb_article,
                    kb_title=text,
                    ltsc_only=False,
                    comment=comment,
                )
            )

    return records


def _parse_hotpatch_page(html: str) -> list[WinBuildNumber]:
    soup = BeautifulSoup(html, "lxml")
    records: list[WinBuildNumber] = []

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                continue

            patch_type = cells[2].get_text(strip=True)
            if "baseline" in patch_type.lower():
                continue

            cell4 = cells[3]
            kb_match = _KB_RE.search(cell4.get_text())
            if not kb_match:
                continue

            href_match = None
            for a in cell4.find_all("a", href=True):
                href_match = _HOTPATCH_HREF_RE.search(a["href"])
                if href_match:
                    break
            if not href_match:
                continue

            month_name = href_match.group(1).capitalize()
            day = href_match.group(2)
            year = href_match.group(3)
            build1 = f"{href_match.group(4)}.{href_match.group(5)}"
            build2 = f"{href_match.group(6)}.{href_match.group(7)}"
            kb_article = kb_match.group(0).upper()

            try:
                from datetime import datetime
                release_date = datetime.strptime(
                    f"{month_name} {day}, {year}", "%B %d, %Y"
                ).strftime("%Y-%m-%d")
            except ValueError:
                continue

            for build in (build1, build2):
                records.append(
                    WinBuildNumber(
                        full_version=f"10.0.{build}",
                        build=build,
                        release_date=release_date,
                        kb_article=kb_article,
                        kb_title=f"{month_name} {day}, {year} — {kb_article} (OS Build {build})",
                        ltsc_only=False,
                        comment="Hotpatch",
                    )
                )

    return records
