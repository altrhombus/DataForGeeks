import re
from datetime import datetime as dt

from bs4 import BeautifulSoup

from src.models.ms.sql_buildnumber import SqlBuildNumber
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://learn.microsoft.com/en-us/sql/database-engine/install-windows/latest-updates-for-microsoft-sql-server"

# Heading: "SQL Server 2022" or "SQL Server 2025"
_VERSION_HEADING_RE = re.compile(r"SQL\s+Server\s+(\d{4})", re.IGNORECASE)
_KB_RE = re.compile(r"KB\d+", re.IGNORECASE)
_DATE_RE = re.compile(r"[A-Za-z]+ \d{1,2}, \d{4}")


class SqlBuildNumbersScraper(BaseScraper):
    dataset = "ms/sql/buildnumbers"
    dataset_name = "sql-server-build-numbers"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")
        records: list[SqlBuildNumber] = []

        current_version = ""
        current_major = 0

        for el in soup.find_all(["h1", "h2", "h3", "h4", "table"]):
            if el.name in ("h1", "h2", "h3", "h4"):
                m = _VERSION_HEADING_RE.search(el.get_text(strip=True))
                if m:
                    current_major = int(m.group(1))
                    current_version = f"SQL Server {current_major}"
                continue

            if not current_version:
                continue

            rows = el.find_all("tr")
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

                build_raw = cells[0].get_text(strip=True)
                sp_raw = cells[1].get_text(strip=True)
                update_raw = cells[2].get_text(strip=True)
                kb_cell = cells[3]
                date_raw = cells[4].get_text(strip=True)

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
                    href = a["href"]
                    if href.startswith("http") and "support.microsoft.com" in href:
                        article_url = href
                        break
                if not article_url and kb_article:
                    article_url = f"https://support.microsoft.com/help/{kb_article[2:]}"

                # Release date
                d_match = _DATE_RE.search(date_raw)
                if not d_match:
                    continue
                try:
                    release_date = dt.strptime(d_match.group(0), "%B %d, %Y").strftime("%Y-%m-%d")
                except ValueError:
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
            raise ValueError("No SQL Server build entries parsed — page structure may have changed")

        seen: set[tuple] = set()
        unique: list[SqlBuildNumber] = []
        for r in sorted(records, key=lambda x: (x.major_version, x.release_date, x.build)):
            key = (r.build, r.release_date)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return [r.model_dump() for r in unique]
