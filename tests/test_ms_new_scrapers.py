"""Tests for the four new MS scrapers: SQL, Exchange, .NET lifecycle, Edge."""

from datetime import date
from pathlib import Path

import pytest

from src.exceptions import StructureChangedError
from src.scrapers.ms.dotnet_lifecycle import _DOTNET_URL, _FRAMEWORK_URL, DotnetLifecycleScraper
from src.scrapers.ms.edge_releases import _ARCHIVE_URL, EdgeReleasesScraper
from src.scrapers.ms.edge_releases import _SOURCE_URL as EDGE_URL
from src.scrapers.ms.exchange_buildnumbers import _SOURCE_URL as EXCH_URL
from src.scrapers.ms.exchange_buildnumbers import ExchangeBuildNumbersScraper
from src.scrapers.ms.sql_buildnumbers import _SOURCE_URL as SQL_URL
from src.scrapers.ms.sql_buildnumbers import SqlBuildNumbersScraper

FIXTURES = Path(__file__).parent / "fixtures" / "ms"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def sql_html() -> str:
    return (FIXTURES / "sql_buildnumbers.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def exchange_html() -> str:
    return (FIXTURES / "exchange_buildnumbers.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dotnet_framework_html() -> str:
    return (FIXTURES / "dotnet_framework_lifecycle.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dotnet_html() -> str:
    return (FIXTURES / "dotnet_lifecycle.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def edge_html() -> str:
    return (FIXTURES / "edge_stable_releases.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def edge_archive_html() -> str:
    return (FIXTURES / "edge_stable_releases_archive.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def sql_pages(sql_html) -> dict[str, str]:
    return {SQL_URL: sql_html}


@pytest.fixture(scope="module")
def exchange_pages(exchange_html) -> dict[str, str]:
    return {EXCH_URL: exchange_html}


@pytest.fixture(scope="module")
def dotnet_pages(dotnet_framework_html, dotnet_html) -> dict[str, str]:
    return {_FRAMEWORK_URL: dotnet_framework_html, _DOTNET_URL: dotnet_html}


@pytest.fixture(scope="module")
def edge_pages(edge_html, edge_archive_html) -> dict[str, str]:
    return {EDGE_URL: edge_html, _ARCHIVE_URL: edge_archive_html}


# ── SQL Server build numbers ───────────────────────────────────────────────────

_SQL_KEYS = {"sql_version", "major_version", "build", "service_pack", "update_type", "kb_article", "release_date", "article_url"}


class TestSqlBuildNumbers:
    def test_returns_records(self, sql_pages):
        records = SqlBuildNumbersScraper().parse(sql_pages)
        assert len(records) > 100

    def test_record_keys(self, sql_pages):
        for r in SqlBuildNumbersScraper().parse(sql_pages):
            assert set(r.keys()) == _SQL_KEYS

    def test_multiple_versions_present(self, sql_pages):
        records = SqlBuildNumbersScraper().parse(sql_pages)
        versions = {r["major_version"] for r in records}
        assert 2022 in versions
        assert 2019 in versions

    def test_release_date_format(self, sql_pages):
        for r in SqlBuildNumbersScraper().parse(sql_pages):
            date.fromisoformat(r["release_date"])

    def test_build_format(self, sql_pages):
        for r in SqlBuildNumbersScraper().parse(sql_pages):
            parts = r["build"].split(".")
            assert len(parts) >= 3
            assert all(p.isdigit() for p in parts)

    def test_kb_article_format(self, sql_pages):
        for r in SqlBuildNumbersScraper().parse(sql_pages):
            if r["kb_article"] is not None:
                assert r["kb_article"].startswith("KB")
                assert r["kb_article"][2:].isdigit()

    def test_no_duplicates(self, sql_pages):
        records = SqlBuildNumbersScraper().parse(sql_pages)
        keys = [(r["build"], r["release_date"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_dataset_slug(self):
        assert SqlBuildNumbersScraper.dataset == "ms/sql/buildnumbers"

    def test_sources_count(self):
        assert len(SqlBuildNumbersScraper.sources) == 1


# ── Exchange Server build numbers ─────────────────────────────────────────────

_EXCH_KEYS = {"product_name", "exchange_version", "build", "build_long", "release_date"}


class TestExchangeBuildNumbers:
    def test_returns_records(self, exchange_pages):
        records = ExchangeBuildNumbersScraper().parse(exchange_pages)
        assert len(records) > 50

    def test_record_keys(self, exchange_pages):
        for r in ExchangeBuildNumbersScraper().parse(exchange_pages):
            assert set(r.keys()) == _EXCH_KEYS

    def test_versions_present(self, exchange_pages):
        records = ExchangeBuildNumbersScraper().parse(exchange_pages)
        versions = {r["exchange_version"] for r in records}
        assert "2019" in versions
        assert "2016" in versions

    def test_release_date_format(self, exchange_pages):
        for r in ExchangeBuildNumbersScraper().parse(exchange_pages):
            date.fromisoformat(r["release_date"])

    def test_build_format(self, exchange_pages):
        for r in ExchangeBuildNumbersScraper().parse(exchange_pages):
            parts = r["build"].split(".")
            assert len(parts) == 4
            assert all(p.isdigit() for p in parts)

    def test_no_duplicates(self, exchange_pages):
        records = ExchangeBuildNumbersScraper().parse(exchange_pages)
        keys = [(r["build"], r["release_date"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_dataset_slug(self):
        assert ExchangeBuildNumbersScraper.dataset == "ms/exchange/buildnumbers"

    def test_sources_count(self):
        assert len(ExchangeBuildNumbersScraper.sources) == 1


# ── .NET lifecycle ─────────────────────────────────────────────────────────────

_DOTNET_KEYS = {"product", "version", "release_date", "end_date"}


class TestDotnetLifecycle:
    def test_returns_records(self, dotnet_pages):
        records = DotnetLifecycleScraper().parse(dotnet_pages)
        assert len(records) > 10

    def test_record_keys(self, dotnet_pages):
        for r in DotnetLifecycleScraper().parse(dotnet_pages):
            assert set(r.keys()) == _DOTNET_KEYS

    def test_both_products_present(self, dotnet_pages):
        records = DotnetLifecycleScraper().parse(dotnet_pages)
        products = {r["product"] for r in records}
        assert ".NET Framework" in products
        assert ".NET" in products

    def test_release_date_format(self, dotnet_pages):
        for r in DotnetLifecycleScraper().parse(dotnet_pages):
            date.fromisoformat(r["release_date"])

    def test_end_date_format_or_none(self, dotnet_pages):
        for r in DotnetLifecycleScraper().parse(dotnet_pages):
            if r["end_date"] is not None:
                date.fromisoformat(r["end_date"])

    def test_no_duplicates(self, dotnet_pages):
        records = DotnetLifecycleScraper().parse(dotnet_pages)
        keys = [(r["product"], r["version"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_dataset_slug(self):
        assert DotnetLifecycleScraper.dataset == "ms/other/dotnet-lifecycle"

    def test_sources_count(self):
        assert len(DotnetLifecycleScraper.sources) == 2


# ── Edge releases ─────────────────────────────────────────────────────────────

_EDGE_KEYS = {"version", "major_version", "release_date"}


class TestEdgeReleases:
    def test_returns_records(self, edge_pages):
        records = EdgeReleasesScraper().parse(edge_pages)
        assert len(records) > 50

    def test_record_keys(self, edge_pages):
        for r in EdgeReleasesScraper().parse(edge_pages):
            assert set(r.keys()) == _EDGE_KEYS

    def test_version_format(self, edge_pages):
        for r in EdgeReleasesScraper().parse(edge_pages):
            parts = r["version"].split(".")
            assert len(parts) == 4
            assert all(p.isdigit() for p in parts)

    def test_major_version_matches_version(self, edge_pages):
        for r in EdgeReleasesScraper().parse(edge_pages):
            assert r["major_version"] == int(r["version"].split(".")[0])

    def test_release_date_format(self, edge_pages):
        for r in EdgeReleasesScraper().parse(edge_pages):
            date.fromisoformat(r["release_date"])

    def test_no_duplicates(self, edge_pages):
        records = EdgeReleasesScraper().parse(edge_pages)
        keys = [(r["version"], r["release_date"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_archive_entries_present(self, edge_pages):
        records = EdgeReleasesScraper().parse(edge_pages)
        # Archive page goes back to at least version 100
        assert any(r["major_version"] < 140 for r in records)

    def test_dataset_slug(self):
        assert EdgeReleasesScraper.dataset == "ms/other/edge-releases"

    def test_sources_count(self):
        assert len(EdgeReleasesScraper.sources) == 2


# ── ValueError guard tests ────────────────────────────────────────────────────

_EMPTY = "<html><body></body></html>"


class TestValueErrorGuards:
    def test_sql_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            SqlBuildNumbersScraper().parse({SQL_URL: _EMPTY})

    def test_exchange_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            ExchangeBuildNumbersScraper().parse({EXCH_URL: _EMPTY})

    def test_dotnet_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            DotnetLifecycleScraper().parse({_FRAMEWORK_URL: _EMPTY, _DOTNET_URL: _EMPTY})

    def test_edge_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            EdgeReleasesScraper().parse({EDGE_URL: _EMPTY, _ARCHIVE_URL: _EMPTY})


# ── Malformed-date tests ───────────────────────────────────────────────────────


class TestMalformedDates:
    def test_exchange_drops_row_with_bad_date(self):
        html = """<html><body>
        <h3>Exchange Server 2019</h3>
        <table>
        <tr><th>Product</th><th>Date</th><th>Build</th><th>Long Build</th></tr>
        <tr><td>Exchange 2019 CU14</td><td>March 1, 2024</td><td>15.2.1544.4</td><td>15.02.1544.004</td></tr>
        <tr><td>Exchange 2019 CU13</td><td>NOT A DATE</td><td>15.2.1258.28</td><td>15.02.1258.028</td></tr>
        </table></body></html>"""
        records = ExchangeBuildNumbersScraper().parse({EXCH_URL: html})
        assert len(records) == 1
        assert records[0]["build"] == "15.2.1544.4"

    def test_edge_drops_version_with_bad_date(self):
        html = """<html><body>
        <h2>## Version 120.0.1234.56: January 10, 2024 (Stable)</h2>
        <h2>## Version 119.0.2151.97: NOT_A_DATE (Stable)</h2>
        </body></html>"""
        records = EdgeReleasesScraper().parse({EDGE_URL: html, _ARCHIVE_URL: _EMPTY})
        assert len(records) == 1
        assert records[0]["version"] == "120.0.1234.56"
