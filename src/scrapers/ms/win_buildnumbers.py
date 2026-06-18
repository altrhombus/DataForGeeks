import logging
import re
from html import unescape

from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.win_buildnumber import WinBuildNumber
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import (
    deduplicate_sorted,
    iter_versioned_tables,
    normalize_ms_url,
    parse_date,
)

logger = logging.getLogger(__name__)

_WIN10_URL = "https://support.microsoft.com/en-us/topic/windows-10-update-history-24ea91f4-36e7-d8fd-0ddb-d79d9d0cdbda"
_WIN11_URL = "https://aka.ms/Windows11UpdateHistory"
_SERVER2016_URL = "https://support.microsoft.com/en-us/topic/windows-10-and-windows-server-2016-update-history-4acfbc84-a290-1b54-536a-1c0430e9f3fd"
_SERVER2019_URL = "https://support.microsoft.com/en-us/topic/windows-10-and-windows-server-2019-update-history-725fc2e1-4443-6831-a5ca-51ff5cbcb059"
_SERVER2022_URL = "https://support.microsoft.com/en-us/topic/windows-server-2022-update-history-e1caa597-00c5-4ab9-9f3e-8212fe80b2ee"
_SERVER2025_URL = "https://support.microsoft.com/en-us/topic/windows-server-2025-update-history-10f58da7-e57b-4a9d-9c16-9f1dcd72d7d7"
_HOTPATCH_URL = "https://support.microsoft.com/en-us/topic/release-notes-for-hotpatch-on-windows-11-enterprise-version-25h2-0bbaa1c7-5070-41ca-a7c9-4ead79602dbf"

# "May 13, 2026—KB5058411 (OS Build 22621.5192)" or multi-build variant
_OS_BUILD_RE = re.compile(
    r"(.+?)\s*\(OS Builds?\s+([\d.,\s]+(?:\s+and\s+[\d.,\s]+)?)\)(.*)",
    re.IGNORECASE,
)

# "May 13, 2026—KB5058411"
_PATCH_DESC_RE = re.compile(
    r"^(.*?\d{1,2}[,]\s*\d{4})\s*[—\-–]+\s*(KB\d+)",
    re.IGNORECASE,
)

# Hotpatch URL slug: "january-14-2025-hotpatch-kb5051978-os-builds-26100-2605-and-26100-2606"
_HOTPATCH_HREF_RE = re.compile(
    r"(\w+)-(\d{1,2})-(\d{4})-hotpatch.*?os-builds?-(\d+)-(\d+)-and-(\d+)-(\d+)",
    re.IGNORECASE,
)
_KB_RE = re.compile(r"KB\d+", re.IGNORECASE)

# Nav category title patterns
_CLIENT_VER_RE = re.compile(r"Windows\s+(?:10|11)\s*[,\s]+[Vv]ersion\s+(\w+)", re.IGNORECASE)
_SERVER_YEAR_RE = re.compile(r"Windows\s+Server\s+(\d{4})", re.IGNORECASE)
_SERVER_ANNUAL_RE = re.compile(r"Windows\s+Server,\s+[Vv]ersion\s+(\w+)", re.IGNORECASE)

# Hotpatch page section heading
_HOTPATCH_VER_RE = re.compile(r"Windows\s+11[,\s]+[Vv]ersion\s+(\w+)", re.IGNORECASE)

# Nav section titles that indicate LTSC or IoT Enterprise variants.
# These sections use the same version extraction as mainstream client sections
# but produce os_type="ltsc" records so they can be routed to LTSC lifecycle data.
_LTSC_TITLE_RE = re.compile(r"\bLTSC\b|\bLTSB\b|Long.Term Servicing|IoT Enterprise", re.IGNORECASE)

_SERVER_ONLY_BUILDS = {"10.0.14393.5127"}


class WinBuildNumbersScraper(BaseScraper):
    """Scrapes Windows 10/11 and Server cumulative update build numbers from support.microsoft.com."""

    dataset = "ms/win/buildnumbers"
    dataset_name = "windows-update-history"
    sources = [_WIN10_URL, _WIN11_URL, _SERVER2016_URL, _SERVER2019_URL, _SERVER2022_URL, _SERVER2025_URL, _HOTPATCH_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[WinBuildNumber] = []

        records.extend(_parse_standard_page(pages[_WIN10_URL], os_type="client", fixed_major=10))
        records.extend(_parse_standard_page(pages[_WIN11_URL], os_type="client", fixed_major=11))
        records.extend(_parse_standard_page(pages[_SERVER2016_URL], os_type="server", fixed_major=None, category_filter="1607"))
        records.extend(_parse_standard_page(pages[_SERVER2019_URL], os_type="server", fixed_major=None, category_filter="1809"))
        records.extend(_parse_standard_page(pages[_SERVER2022_URL], os_type="server", fixed_major=None))
        records.extend(_parse_standard_page(pages[_SERVER2025_URL], os_type="server", fixed_major=None, category_filter="2025"))
        records.extend(_parse_hotpatch_page(pages[_HOTPATCH_URL]))

        if not records:
            raise StructureChangedError("No build entries parsed — page structure may have changed")

        # Dedup: one record per (full_version, os_type). Sort ascending by (release_date, build)
        # so the earliest occurrence wins — the first release of any base build is always from
        # the nav section that introduced it, giving the correct windows_version label.
        unique = deduplicate_sorted(records, sort_key=lambda r: (r.release_date, r.build), key_fn=lambda r: (r.full_version, r.os_type))

        unique = [r for r in unique if r.full_version not in _SERVER_ONLY_BUILDS]

        # KB-level IsExpired normalization: if any record for a KB is expired, all are
        expired_kbs: set[str] = {r.kb_article for r in unique if r.is_expired}
        if expired_kbs:
            for r in unique:
                if not r.is_expired and r.kb_article in expired_kbs:
                    object.__setattr__(r, "is_expired", True)  # bypass frozen=True intentionally

        # Canonical version normalization: for each (base_build, os_type), the windows_version
        # from the earliest-ever release is the canonical label. Reassigns minority entries that
        # accumulated during multi-version combined-CU overlap periods (e.g. build 19044 entries
        # labeled "22H2" from the Oct 2022–Jun 2023 overlap window).
        earliest_ver: dict[tuple[str, str], tuple[str, str]] = {}
        for r in unique:
            base = r.build.split(".")[0] if "." in r.build else r.build
            key = (base, r.os_type)
            if key not in earliest_ver or r.release_date < earliest_ver[key][0]:
                earliest_ver[key] = (r.release_date, r.windows_version)

        canonical_ver = {k: v[1] for k, v in earliest_ver.items()}

        for r in unique:
            base = r.build.split(".")[0] if "." in r.build else r.build
            canon = canonical_ver.get((base, r.os_type), r.windows_version)
            if r.windows_version != canon:
                object.__setattr__(r, "windows_version", canon)  # bypass frozen=True intentionally

        return [r.model_dump() for r in unique]


def _parse_standard_page(
    html: str,
    os_type: str,
    fixed_major: int | None,
    category_filter: str | None = None,
) -> list[WinBuildNumber]:
    """Parse a Windows update history page using the supLeftNavCategory nav structure.

    category_filter: if set, only process categories whose title contains this substring.
    Used for combined Win10+Server pages to isolate the server-specific section.
    """
    soup = BeautifulSoup(html, "lxml")
    records: list[WinBuildNumber] = []

    for category in soup.find_all("div", class_="supLeftNavCategory"):
        title_div = category.find("div", class_="supLeftNavCategoryTitle")
        if not title_div:
            continue

        title_text = title_div.get_text(strip=True)

        if category_filter and category_filter not in title_text:
            continue

        if os_type == "client":
            m = _CLIENT_VER_RE.search(title_text)
            if not m or fixed_major is None:
                continue
            current_version = m.group(1).upper()
            current_major = fixed_major
            # LTSC and IoT Enterprise nav sections use the same version extraction but
            # get os_type="ltsc" so they can be joined to LTSC lifecycle data downstream.
            section_os_type = "ltsc" if _LTSC_TITLE_RE.search(title_text) else "client"
        else:
            m_year = _SERVER_YEAR_RE.search(title_text)
            m_annual = _SERVER_ANNUAL_RE.search(title_text)

            if m_year:
                current_major = int(m_year.group(1))
                # Combined pages (e.g. "1607 and Server 2016") — version from client pattern
                m_client = _CLIENT_VER_RE.search(title_text)
                current_version = m_client.group(1).upper() if m_client else m_year.group(1)
            elif m_annual:
                current_version = m_annual.group(1).upper()
                current_major = 2022  # Annual Channel belongs to Server 2022
            else:
                continue
            section_os_type = os_type

        for article in category.find_all("li", class_="supLeftNavArticle"):
            a = article.find("a")
            if not a:
                continue

            text = unescape(a.get_text(strip=True))
            m = _OS_BUILD_RE.match(text)
            if not m:
                continue

            description = m.group(1).strip()
            versions_raw = m.group(2)
            suffix = m.group(3).strip()

            pd = _PATCH_DESC_RE.match(description)
            if not pd:
                continue

            release_date = parse_date(pd.group(1).strip())
            if not release_date:
                logger.warning("Skipping row: could not parse date %r", pd.group(1).strip())
                continue

            kb_article = pd.group(2).upper()

            suffix_up = suffix.upper()
            desc_up = description.upper()
            is_expired = "EXPIRED" in suffix_up
            is_oob = "OUT-OF-BAND" in suffix_up
            is_preview = "PREVIEW" in suffix_up or "PREVIEW" in desc_up
            release_type = "Out-of-band" if is_oob else "Preview" if is_preview else "Standard"

            article_url = normalize_ms_url(str(a.get("href") or ""))

            for version in [v.strip() for v in re.split(r"\s+and\s+|,", versions_raw) if v.strip()]:
                records.append(
                    WinBuildNumber(
                        full_version=f"10.0.{version}",
                        build=version,
                        os_type=section_os_type,
                        major_version=current_major,
                        windows_version=current_version,
                        release_date=release_date,
                        kb_article=kb_article,
                        release_type=release_type,
                        is_expired=is_expired,
                        article_url=article_url,
                    )
                )

    return records


def _parse_hotpatch_page(html: str) -> list[WinBuildNumber]:
    soup = BeautifulSoup(html, "lxml")
    records: list[WinBuildNumber] = []

    for version_raw, table in iter_versioned_tables(soup, _HOTPATCH_VER_RE, skip_unversioned=False):
        current_version = version_raw.upper() if version_raw else ""
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                continue

            patch_type = cells[2].get_text(strip=True).lower()  # col 2: Patch Type (Baseline / Standard / OOB)
            if "baseline" in patch_type:
                continue

            cell4 = cells[3]  # col 3: KB article number + href
            kb_match = _KB_RE.search(cell4.get_text())
            if not kb_match:
                continue

            href_match = None
            article_url = None
            for a in cell4.find_all("a", href=True):
                hm = _HOTPATCH_HREF_RE.search(str(a["href"]))
                if hm:
                    href_match = hm
                    article_url = normalize_ms_url(str(a["href"]))
                    break
            if not href_match:
                continue

            month_name = href_match.group(1).capitalize()
            day = href_match.group(2)
            year = href_match.group(3)
            build1 = f"{href_match.group(4)}.{href_match.group(5)}"
            build2 = f"{href_match.group(6)}.{href_match.group(7)}"
            kb_article = kb_match.group(0).upper()

            release_date = parse_date(f"{month_name} {day}, {year}")
            if not release_date:
                logger.warning("Skipping row: could not parse date %r", f"{month_name} {day}, {year}")
                continue

            is_oob = "out-of-band" in patch_type or "oob" in patch_type
            release_type = "Hotpatch-OOB" if is_oob else "Hotpatch"

            for build in (build1, build2):
                records.append(
                    WinBuildNumber(
                        full_version=f"10.0.{build}",
                        build=build,
                        os_type="client",
                        major_version=11,
                        windows_version=current_version or "25H2",
                        release_date=release_date,
                        kb_article=kb_article,
                        release_type=release_type,
                        is_expired=False,
                        article_url=article_url,
                    )
                )

    return records
