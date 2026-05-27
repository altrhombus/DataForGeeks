import json
from datetime import date, timedelta

from src.models.linux.ubuntu_release import UbuntuRelease
from src.scrapers.base import BaseScraper

_API_URL = "https://api.launchpad.net/1.0/ubuntu/series?ws.size=75"


def _is_lts(version: str) -> bool:
    # Dapper Drake (6.06) was an LTS despite being a June release
    if version == "6.06":
        return True
    parts = version.split(".")
    if len(parts) == 2:
        year, month = int(parts[0]), int(parts[1])
        return month == 4 and year % 2 == 0
    return False


def _add_years(d: date, years: int) -> str:
    try:
        return d.replace(year=d.year + years).isoformat()
    except ValueError:
        # Feb 29 edge case
        return d.replace(year=d.year + years, day=28).isoformat()


def _add_months(d: date, months: int) -> str:
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    last_day = (date(year, month % 12 + 1, 1) - timedelta(days=1)).day if month != 12 else 31
    day = min(d.day, last_day)
    return date(year, month, day).isoformat()


class UbuntuReleasesScraper(BaseScraper):
    dataset = "linux/ubuntu/releases"
    dataset_name = "ubuntu-releases"
    sources = [_API_URL]

    def parse(self, pages: dict[str, str]) -> list[dict]:
        raw = json.loads(pages[_API_URL])
        entries = raw.get("entries", [])

        records: list[UbuntuRelease] = []
        for entry in entries:
            date_str = entry.get("datereleased")
            if not date_str:
                continue  # skip unreleased series
            release_date = date_str[:10]  # "2020-04-23T00:00:00+00:00" → "2020-04-23"
            version = entry["version"]
            lts = _is_lts(version)
            rd = date.fromisoformat(release_date)

            standard_support_end = _add_years(rd, 5) if lts else _add_months(rd, 9)
            esm_support_end = _add_years(rd, 10) if lts else None

            codename = entry["title"]
            if codename.startswith("The "):
                codename = codename[4:]
            records.append(UbuntuRelease(
                version=version,
                codename=codename,
                series=entry["name"],
                release_date=release_date,
                status=entry["status"],
                is_lts=lts,
                standard_support_end=standard_support_end,
                esm_support_end=esm_support_end,
            ))

        if not records:
            raise ValueError("No Ubuntu release entries parsed — API response may have changed")

        return [r.model_dump() for r in sorted(records, key=lambda x: x.release_date, reverse=True)]
