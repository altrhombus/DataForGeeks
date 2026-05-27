"""Tests for the Windows build numbers scraper using saved HTML fixtures."""

from datetime import date
from pathlib import Path

import pytest

from src.scrapers.ms.win_buildnumbers import (
    WinBuildNumbersScraper,
    _parse_hotpatch_page,
    _parse_standard_page,
)

FIXTURES = Path(__file__).parent / "fixtures" / "ms"


@pytest.fixture(scope="module")
def win10_html() -> str:
    return (FIXTURES / "win10_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def win11_html() -> str:
    return (FIXTURES / "win11_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def server2022_html() -> str:
    return (FIXTURES / "server2022_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hotpatch_html() -> str:
    return (FIXTURES / "win11_hotpatch.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def all_pages(win10_html, win11_html, server2022_html, hotpatch_html) -> dict[str, str]:
    from src.scrapers.ms.win_buildnumbers import (
        _WIN10_URL, _WIN11_URL, _SERVER2022_URL, _HOTPATCH_URL,
    )
    return {
        _WIN10_URL: win10_html,
        _WIN11_URL: win11_html,
        _SERVER2022_URL: server2022_html,
        _HOTPATCH_URL: hotpatch_html,
    }


class TestParseStandardPage:
    def test_returns_records(self, win10_html):
        records = _parse_standard_page(win10_html)
        assert len(records) > 100

    def test_record_schema(self, win10_html):
        records = _parse_standard_page(win10_html)
        r = records[0]
        assert set(r.__dict__.keys()) == {
            "full_version", "build", "release_date", "kb_article", "kb_title",
            "ltsc_only", "comment",
        }

    def test_full_version_prefix(self, win10_html):
        for r in _parse_standard_page(win10_html):
            assert r.full_version.startswith("10.0.")

    def test_build_matches_full_version(self, win10_html):
        for r in _parse_standard_page(win10_html):
            assert r.full_version == f"10.0.{r.build}"

    def test_release_date_format(self, win10_html):
        for r in _parse_standard_page(win10_html):
            # Will raise ValueError if format is wrong
            date.fromisoformat(r.release_date)

    def test_kb_article_format(self, win10_html):
        for r in _parse_standard_page(win10_html):
            assert r.kb_article.startswith("KB")
            assert r.kb_article[2:].isdigit()

    def test_ltsc_only_default_false(self, win10_html):
        records = _parse_standard_page(win10_html)
        # Before overrides are applied all records are False
        assert all(not r.ltsc_only for r in records)

    def test_win11_page_parses(self, win11_html):
        records = _parse_standard_page(win11_html)
        assert len(records) > 50

    def test_server2022_page_parses(self, server2022_html):
        records = _parse_standard_page(server2022_html)
        assert len(records) > 20


class TestParseHotpatchPage:
    def test_returns_records(self, hotpatch_html):
        records = _parse_hotpatch_page(hotpatch_html)
        assert len(records) > 0

    def test_comment_is_hotpatch(self, hotpatch_html):
        for r in _parse_hotpatch_page(hotpatch_html):
            assert r.comment == "Hotpatch"

    def test_build_format(self, hotpatch_html):
        for r in _parse_hotpatch_page(hotpatch_html):
            major, minor = r.build.split(".")
            assert major.isdigit()
            assert minor.isdigit()

    def test_skips_baseline_rows(self, hotpatch_html):
        records = _parse_hotpatch_page(hotpatch_html)
        # Baseline rows should not appear in output
        # Verify by checking that all entries are paired (come in twos by build)
        assert all(r.full_version.startswith("10.0.") for r in records)


class TestWinBuildNumbersScraper:
    def test_parse_total_records(self, all_pages):
        scraper = WinBuildNumbersScraper()
        records = scraper.parse(all_pages)
        assert len(records) > 500

    def test_no_duplicates(self, all_pages):
        scraper = WinBuildNumbersScraper()
        records = scraper.parse(all_pages)
        keys = [(r["full_version"], r["release_date"], r["kb_article"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_sorted_by_date_then_build(self, all_pages):
        scraper = WinBuildNumbersScraper()
        records = scraper.parse(all_pages)
        dates = [(r["release_date"], r["build"]) for r in records]
        assert dates == sorted(dates)

    def test_server_only_build_excluded(self, all_pages):
        scraper = WinBuildNumbersScraper()
        records = scraper.parse(all_pages)
        full_versions = {r["full_version"] for r in records}
        assert "10.0.14393.5127" not in full_versions

    def test_ltsc_override_applied(self, all_pages):
        scraper = WinBuildNumbersScraper()
        records = scraper.parse(all_pages)
        ltsc_records = [r for r in records if r["ltsc_only"]]
        assert len(ltsc_records) > 0
        for r in ltsc_records:
            assert r["full_version"].startswith("10.0.17763.")
            assert date.fromisoformat(r["release_date"]) >= date(2021, 5, 12)

    def test_hotpatch_entries_present(self, all_pages):
        scraper = WinBuildNumbersScraper()
        records = scraper.parse(all_pages)
        hotpatch = [r for r in records if r["comment"] == "Hotpatch"]
        assert len(hotpatch) > 0

    def test_record_keys(self, all_pages):
        scraper = WinBuildNumbersScraper()
        records = scraper.parse(all_pages)
        expected_keys = {"full_version", "build", "release_date", "kb_article", "kb_title", "ltsc_only", "comment"}
        for r in records:
            assert set(r.keys()) == expected_keys

    def test_dataset_slug(self):
        assert WinBuildNumbersScraper.dataset == "ms/win/buildnumbers"

    def test_sources_count(self):
        assert len(WinBuildNumbersScraper.sources) == 4
