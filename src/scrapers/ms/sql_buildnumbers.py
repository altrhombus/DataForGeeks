import logging
import re

from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.sql_buildnumber import SqlBuildNumber
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import (
    deduplicate_sorted,
    iter_versioned_tables,
    normalize_ms_url,
    parse_date,
)

logger = logging.getLogger(__name__)

_SOURCE_URL = "https://learn.microsoft.com/en-us/sql/database-engine/install-windows/latest-updates-for-microsoft-sql-server"

# Heading: "SQL Server 2022" or "SQL Server 2025"
_VERSION_HEADING_RE = re.compile(r"SQL\s+Server\s+(\d{4})", re.IGNORECASE)
_KB_RE = re.compile(r"KB\d+", re.IGNORECASE)
_DATE_RE = re.compile(r"[A-Za-z]+ \d{1,2}, \d{4}")


class SqlBuildNumbersScraper(BaseScraper):
    """Scrapes SQL Server build numbers, KB articles, and release dates from learn.microsoft.com."""

    dataset = "ms/sql/buildnumbers"
    dataset_name = "sql-server-build-numbers"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")
        records: list[SqlBuildNumber] = []

        for version_raw, table in iter_versioned_tables(soup, _VERSION_HEADING_RE):
            current_major = int(version_raw)
            current_version = f"SQL Server {current_major}"
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            # Validate header row contains expected columns
            header = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
            if not any("build" in h or "version" in h for h in header):
                continue

            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue

                build_raw = cells[0].get_text(strip=True)   # col 0: Build number
                sp_raw = cells[1].get_text(strip=True)      # col 1: Service pack label
                update_raw = cells[2].get_text(strip=True)  # col 2: Update type (CU, GDR, RTM)
                kb_cell = cells[3]                          # col 3: KB article number + href
                date_raw = cells[4].get_text(strip=True)    # col 4: Release date

                # Build must look like a version number
                if not re.match(r"\d+\.\d+", build_raw):
                    continue

                # KB
                kb_text = kb_cell.get_text(strip=True)
                kb_match = _KB_RE.search(kb_text)
                kb_article = kb_match.group(0).upper() if kb_match else None

                # Article URL — prefer support.microsoft.com links, fall back to KB number
                article_url: str | None = None
                for a in kb_cell.find_all("a", href=True):
                    candidate = normalize_ms_url(str(a["href"]))
                    if candidate and "support.microsoft.com" in candidate:
                        article_url = candidate
                        break
                if not article_url and kb_article:
                    article_url = f"https://support.microsoft.com/help/{kb_article[2:]}"

                # Release date
                d_match = _DATE_RE.search(date_raw)
                if not d_match:
                    continue
                release_date = parse_date(d_match.group(0))
                if not release_date:
                    logger.warning("Skipping row: could not parse date %r", d_match.group(0))
                    continue

                sp = sp_raw if sp_raw and sp_raw.upper() not in ("NONE", "N/A", "-") else None
                update_type = update_raw or "RTM"

                records.append(
                    SqlBuildNumber(
                        sql_version=current_version,
                        major_version=current_major,
                        build=build_raw,
                        service_pack=sp,
                        update_type=update_type,
                        kb_article=kb_article,
                        release_date=release_date,
                        article_url=article_url,
                    )
                )

        if not records:
            raise StructureChangedError("No SQL Server build entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: (r.major_version, r.release_date, r.build), key_fn=lambda r: (r.build, r.release_date))
        return [r.model_dump() for r in unique]
