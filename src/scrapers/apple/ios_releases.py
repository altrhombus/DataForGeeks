import re
from datetime import datetime as dt

from bs4 import BeautifulSoup

from src.models.apple.ios_release import IosRelease
from src.scrapers.base import BaseScraper

_SOURCE_URL = "https://support.apple.com/en-us/100100"
_ARCHIVE_URL = "https://support.apple.com/en-us/121012"

# "iOS 17.2.1" or "iPadOS 17.7.11"
_IOS_IPAD_RE = re.compile(r"^(iOS|iPadOS)\s+([\d.]+)", re.IGNORECASE)
# "iOS 17.2.1 and iPadOS 17.2.1" — combined entry
_COMBINED_RE = re.compile(r"^iOS\s+([\d.]+)\s+and\s+iPadOS\s+([\d.]+)", re.IGNORECASE)


def _parse_apple_page(html: str) -> list[IosRelease]:
    soup = BeautifulSoup(html, "lxml")
    records: list[IosRelease] = []
    for row in soup.select("table tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        name = cells[0].get_text(separator=" ", strip=True)
        date_text = cells[2].get_text(strip=True)
        try:
            release_date = dt.strptime(date_text, "%d %b %Y").strftime("%Y-%m-%d")
        except ValueError:
            try:
                release_date = dt.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")
            except ValueError:
                continue

        combined = _COMBINED_RE.match(name)
        if combined:
            ios_ver = combined.group(1)
            ipad_ver = combined.group(2)
            records.append(IosRelease(
                product="iOS",
                version=ios_ver,
                major_version=int(ios_ver.split(".")[0]),
                release_date=release_date,
            ))
            records.append(IosRelease(
                product="iPadOS",
                version=ipad_ver,
                major_version=int(ipad_ver.split(".")[0]),
                release_date=release_date,
            ))
            continue

        m = _IOS_IPAD_RE.match(name)
        if not m:
            continue
        product = m.group(1)
        # Normalise capitalisation
        product = "iOS" if product.lower() == "ios" else "iPadOS"
        version = m.group(2)
        records.append(IosRelease(
            product=product,
            version=version,
            major_version=int(version.split(".")[0]),
            release_date=release_date,
        ))
    return records


class IosReleasesScraper(BaseScraper):
    dataset = "apple/ios/releases"
    dataset_name = "ios-releases"
    sources = [_SOURCE_URL, _ARCHIVE_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        records: list[IosRelease] = []
        records.extend(_parse_apple_page(pages[_SOURCE_URL]))
        records.extend(_parse_apple_page(pages[_ARCHIVE_URL]))

        if not records:
            raise ValueError("No iOS/iPadOS release entries parsed — page structure may have changed")

        seen: set[tuple] = set()
        unique: list[IosRelease] = []
        for r in sorted(records, key=lambda x: (x.release_date, x.product, x.version)):
            key = (r.product, r.version, r.release_date)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return [r.model_dump() for r in unique]
