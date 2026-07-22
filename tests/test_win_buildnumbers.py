"""Tests for the Windows build numbers scraper using saved HTML fixtures."""

from datetime import date
from pathlib import Path

import pytest

from src.exceptions import StructureChangedError
from src.scrapers.ms.win_buildnumbers import (
    _HOTPATCH_URL,
    _SERVER2016_URL,
    _SERVER2019_URL,
    _SERVER2022_URL,
    _SERVER2025_URL,
    _WIN10_URL,
    _WIN11_URL,
    WinBuildNumbersScraper,
    _parse_hotpatch_page,
    _parse_standard_page,
)

FIXTURES = Path(__file__).parent / "fixtures" / "ms"

_EXPECTED_KEYS = {
    "full_version", "build", "os_type", "major_version", "windows_version",
    "release_date", "kb_article", "release_type", "is_expired", "article_url",
}


@pytest.fixture(scope="module")
def win10_html() -> str:
    return (FIXTURES / "win10_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def win11_html() -> str:
    return (FIXTURES / "win11_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def server2016_html() -> str:
    return (FIXTURES / "server2016_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def server2019_html() -> str:
    return (FIXTURES / "server2019_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def server2022_html() -> str:
    return (FIXTURES / "server2022_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def server2025_html() -> str:
    return (FIXTURES / "server2025_update_history.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hotpatch_html() -> str:
    return (FIXTURES / "win11_hotpatch.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def all_pages(win10_html, win11_html, server2016_html, server2019_html, server2022_html, server2025_html, hotpatch_html) -> dict[str, str]:
    return {
        _WIN10_URL: win10_html,
        _WIN11_URL: win11_html,
        _SERVER2016_URL: server2016_html,
        _SERVER2019_URL: server2019_html,
        _SERVER2022_URL: server2022_html,
        _SERVER2025_URL: server2025_html,
        _HOTPATCH_URL: hotpatch_html,
    }


class TestParseStandardPage:
    def test_returns_records(self, win10_html):
        records = _parse_standard_page(win10_html, os_type="client", fixed_major=10)
        assert len(records) > 100

    def test_record_schema(self, win10_html):
        records = _parse_standard_page(win10_html, os_type="client", fixed_major=10)
        assert set(records[0].model_dump().keys()) == _EXPECTED_KEYS

    def test_full_version_prefix(self, win10_html):
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert r.full_version.startswith("10.0.")

    def test_build_matches_full_version(self, win10_html):
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert r.full_version == f"10.0.{r.build}"

    def test_release_date_format(self, win10_html):
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            date.fromisoformat(r.release_date)

    def test_kb_article_format(self, win10_html):
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert r.kb_article.startswith("KB")
            assert r.kb_article[2:].isdigit()

    def test_os_type_client(self, win10_html):
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert r.os_type == "client"

    def test_major_version_win10(self, win10_html):
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert r.major_version == 10

    def test_windows_version_populated(self, win10_html):
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert r.windows_version != ""

    def test_release_type_valid(self, win10_html):
        valid = {"Standard", "Preview", "Out-of-band"}
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert r.release_type in valid

    def test_is_expired_is_bool(self, win10_html):
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert isinstance(r.is_expired, bool)

    def test_article_url_never_null(self, win10_html):
        # Regression guard: the 2026-07 site redesign switched hrefs to relative
        # paths, silently nulling every href-derived article_url.
        for r in _parse_standard_page(win10_html, os_type="client", fixed_major=10):
            assert r.article_url is not None
            assert r.article_url == f"https://support.microsoft.com/help/{r.kb_article[2:]}"

    def test_win11_page_parses(self, win11_html):
        records = _parse_standard_page(win11_html, os_type="client", fixed_major=11)
        assert len(records) > 50

    def test_win11_major_version(self, win11_html):
        for r in _parse_standard_page(win11_html, os_type="client", fixed_major=11):
            assert r.major_version == 11

    def test_server2016_page_parses(self, server2016_html):
        records = _parse_standard_page(server2016_html, os_type="server", fixed_major=None, category_filter="1607")
        assert len(records) > 20

    def test_server2016_major_version(self, server2016_html):
        for r in _parse_standard_page(server2016_html, os_type="server", fixed_major=None, category_filter="1607"):
            assert r.major_version == 2016

    def test_server2016_windows_version(self, server2016_html):
        for r in _parse_standard_page(server2016_html, os_type="server", fixed_major=None, category_filter="1607"):
            assert r.windows_version == "1607"

    def test_server2019_page_parses(self, server2019_html):
        records = _parse_standard_page(server2019_html, os_type="server", fixed_major=None, category_filter="1809")
        assert len(records) > 20

    def test_server2019_major_version(self, server2019_html):
        for r in _parse_standard_page(server2019_html, os_type="server", fixed_major=None, category_filter="1809"):
            assert r.major_version == 2019

    def test_server2019_windows_version(self, server2019_html):
        for r in _parse_standard_page(server2019_html, os_type="server", fixed_major=None, category_filter="1809"):
            assert r.windows_version == "1809"

    def test_server2022_page_parses(self, server2022_html):
        records = _parse_standard_page(server2022_html, os_type="server", fixed_major=None)
        assert len(records) > 20

    def test_server2025_page_parses(self, server2025_html):
        records = _parse_standard_page(server2025_html, os_type="server", fixed_major=None, category_filter="2025")
        assert len(records) > 20

    def test_server2025_major_version(self, server2025_html):
        for r in _parse_standard_page(server2025_html, os_type="server", fixed_major=None, category_filter="2025"):
            assert r.major_version == 2025

    def test_server2025_windows_version(self, server2025_html):
        for r in _parse_standard_page(server2025_html, os_type="server", fixed_major=None, category_filter="2025"):
            assert r.windows_version == "2025"

    def test_server_os_type(self, server2022_html):
        for r in _parse_standard_page(server2022_html, os_type="server", fixed_major=None):
            assert r.os_type == "server"


class TestParseHotpatchPage:
    def test_returns_records(self, hotpatch_html):
        records = _parse_hotpatch_page(hotpatch_html)
        assert len(records) > 0

    def test_release_type_hotpatch(self, hotpatch_html):
        for r in _parse_hotpatch_page(hotpatch_html):
            assert r.release_type in {"Hotpatch", "Hotpatch-OOB"}

    def test_os_type_client(self, hotpatch_html):
        for r in _parse_hotpatch_page(hotpatch_html):
            assert r.os_type == "client"

    def test_major_version_11(self, hotpatch_html):
        for r in _parse_hotpatch_page(hotpatch_html):
            assert r.major_version == 11

    def test_build_format(self, hotpatch_html):
        for r in _parse_hotpatch_page(hotpatch_html):
            major, minor = r.build.split(".")
            assert major.isdigit() and minor.isdigit()

    def test_full_version_prefix(self, hotpatch_html):
        for r in _parse_hotpatch_page(hotpatch_html):
            assert r.full_version.startswith("10.0.")


class TestWinBuildNumbersScraper:
    def test_parse_total_records(self, all_pages):
        records = WinBuildNumbersScraper().parse(all_pages)
        assert len(records) > 500

    def test_record_keys(self, all_pages):
        for r in WinBuildNumbersScraper().parse(all_pages):
            assert set(r.keys()) == _EXPECTED_KEYS

    def test_no_duplicates(self, all_pages):
        records = WinBuildNumbersScraper().parse(all_pages)
        # os_type is part of the dedup key: shared builds (e.g. 14393.x) coexist as client + server
        keys = [(r["full_version"], r["release_date"], r["kb_article"], r["os_type"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_sorted_by_date_then_build(self, all_pages):
        records = WinBuildNumbersScraper().parse(all_pages)
        dates = [(r["release_date"], r["build"]) for r in records]
        assert dates == sorted(dates)

    def test_server_only_build_excluded(self, all_pages):
        full_versions = {r["full_version"] for r in WinBuildNumbersScraper().parse(all_pages)}
        assert "10.0.14393.5127" not in full_versions

    def test_hotpatch_entries_present(self, all_pages):
        records = WinBuildNumbersScraper().parse(all_pages)
        hotpatch = [r for r in records if r["release_type"] in {"Hotpatch", "Hotpatch-OOB"}]
        assert len(hotpatch) > 0

    def test_all_article_urls_populated(self, all_pages):
        records = WinBuildNumbersScraper().parse(all_pages)
        assert all(r["article_url"] for r in records)

    def test_os_types_present(self, all_pages):
        records = WinBuildNumbersScraper().parse(all_pages)
        os_types = {r["os_type"] for r in records}
        assert "client" in os_types
        assert "server" in os_types

    def test_is_expired_propagation(self, all_pages):
        records = WinBuildNumbersScraper().parse(all_pages)
        expired_kbs = {r["kb_article"] for r in records if r["is_expired"]}
        for r in records:
            if r["kb_article"] in expired_kbs:
                assert r["is_expired"], f"{r['kb_article']} should be expired for all builds"

    def test_dataset_slug(self):
        assert WinBuildNumbersScraper.dataset == "ms/win/buildnumbers"

    def test_dataset_name(self):
        assert WinBuildNumbersScraper.dataset_name == "windows-update-history"

    def test_sources_count(self):
        assert len(WinBuildNumbersScraper.sources) == 7


# ── ValueError guard test ─────────────────────────────────────────────────────

_EMPTY = "<html><body></body></html>"


class TestValueErrorGuard:
    def test_raises_on_empty_html(self):
        pages = {
            _WIN10_URL: _EMPTY,
            _WIN11_URL: _EMPTY,
            _SERVER2016_URL: _EMPTY,
            _SERVER2019_URL: _EMPTY,
            _SERVER2022_URL: _EMPTY,
            _SERVER2025_URL: _EMPTY,
            _HOTPATCH_URL: _EMPTY,
        }
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            WinBuildNumbersScraper().parse(pages)
