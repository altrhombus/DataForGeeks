import logging
import re

from bs4 import BeautifulSoup

from src.exceptions import StructureChangedError
from src.models.ms.exchange_buildnumber import ExchangeBuildNumber
from src.scrapers.base import BaseScraper
from src.utils.scraper_helpers import deduplicate_sorted, iter_versioned_tables, parse_date

logger = logging.getLogger(__name__)

_SOURCE_URL = "https://learn.microsoft.com/en-us/exchange/new-features/build-numbers-and-release-dates"

# Heading: "Exchange Server SE", "Exchange Server 2019"
_VERSION_HEADING_RE = re.compile(r"Exchange\s+Server\s+(SE|\d{4})", re.IGNORECASE)
_DATE_RE = re.compile(r"[A-Za-z]+ \d{1,2}, \d{4}")


class ExchangeBuildNumbersScraper(BaseScraper):
    """Scrapes Exchange Server build numbers and release dates from learn.microsoft.com."""

    dataset = "ms/exchange/buildnumbers"
    dataset_name = "exchange-server-build-numbers"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")
        records: list[ExchangeBuildNumber] = []

        for version_raw, table in iter_versioned_tables(soup, _VERSION_HEADING_RE):
            current_version = version_raw.upper()
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            header = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
            if not any("build" in h or "product" in h for h in header):
                continue

            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue

                product_name = cells[0].get_text(strip=True)   # col 0: Product name
                date_raw = cells[1].get_text(strip=True)        # col 1: Release date
                build = cells[2].get_text(strip=True)           # col 2: Build number (short)
                build_long = cells[3].get_text(strip=True)      # col 3: Build number (long)

                if not product_name or not build:
                    continue

                # Build must look like a version number
                if not re.match(r"\d+\.\d+", build):
                    continue

                d_match = _DATE_RE.search(date_raw)
                if not d_match:
                    continue
                release_date = parse_date(d_match.group(0))
                if not release_date:
                    logger.warning("Skipping row: could not parse date %r", d_match.group(0))
                    continue

                records.append(
                    ExchangeBuildNumber(
                        product_name=product_name,
                        exchange_version=current_version,
                        build=build,
                        build_long=build_long,
                        release_date=release_date,
                    )
                )

        if not records:
            raise StructureChangedError("No Exchange build entries parsed — page structure may have changed")

        unique = deduplicate_sorted(records, sort_key=lambda r: (r.exchange_version, r.release_date, r.build), key_fn=lambda r: (r.build, r.release_date))
        return [r.model_dump() for r in unique]
