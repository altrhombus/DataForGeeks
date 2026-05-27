import re
from datetime import datetime as dt

from bs4 import BeautifulSoup

from src.models.ms.exchange_buildnumber import ExchangeBuildNumber
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://learn.microsoft.com/en-us/exchange/new-features/build-numbers-and-release-dates"

# Heading: "Exchange Server SE", "Exchange Server 2019"
_VERSION_HEADING_RE = re.compile(r"Exchange\s+Server\s+(SE|\d{4})", re.IGNORECASE)
_DATE_RE = re.compile(r"[A-Za-z]+ \d{1,2}, \d{4}")


class ExchangeBuildNumbersScraper(BaseScraper):
    dataset = "ms/exchange/buildnumbers"
    dataset_name = "exchange-server-build-numbers"
    sources = [_SOURCE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        soup = BeautifulSoup(pages[_SOURCE_URL], "lxml")
        records: list[ExchangeBuildNumber] = []

        current_version = ""

        for el in soup.find_all(["h1", "h2", "h3", "h4", "table"]):
            if el.name in ("h1", "h2", "h3", "h4"):
                m = _VERSION_HEADING_RE.search(el.get_text(strip=True))
                if m:
                    current_version = m.group(1).upper()
                continue

            if not current_version:
                continue

            rows = el.find_all("tr")
            if len(rows) < 2:
                continue

            header = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
            if not any("build" in h or "product" in h for h in header):
                continue

            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue

                product_name = cells[0].get_text(strip=True)
                date_raw = cells[1].get_text(strip=True)
                build = cells[2].get_text(strip=True)
                build_long = cells[3].get_text(strip=True)

                if not product_name or not build:
                    continue

                # Build must look like a version number
                if not re.match(r"\d+\.\d+", build):
                    continue

                d_match = _DATE_RE.search(date_raw)
                if not d_match:
                    continue
                try:
                    release_date = dt.strptime(d_match.group(0), "%B %d, %Y").strftime("%Y-%m-%d")
                except ValueError:
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
            raise ValueError("No Exchange build entries parsed — page structure may have changed")

        seen: set[tuple] = set()
        unique: list[ExchangeBuildNumber] = []
        for r in sorted(records, key=lambda x: (x.exchange_version, x.release_date, x.build)):
            key = (r.build, r.release_date)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return [r.model_dump() for r in unique]
