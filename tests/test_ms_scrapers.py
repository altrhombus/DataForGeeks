"""Tests for the remaining 10 MS scrapers using saved HTML fixtures."""

import re
from pathlib import Path

import pytest

from src.exceptions import StructureChangedError
from src.scrapers.ms.asr_guids import _SOURCE_URL as ASR_URL
from src.scrapers.ms.asr_guids import AsrGuidsScraper
from src.scrapers.ms.bitlocker_volume_types import _SOURCE_URL as BL_URL
from src.scrapers.ms.bitlocker_volume_types import BitlockerVolumeTypesScraper
from src.scrapers.ms.chassis_types import _SOURCE_URL as CHASSIS_URL
from src.scrapers.ms.chassis_types import ChassisTypesScraper
from src.scrapers.ms.locales import _SOURCE_URL as LOCALES_URL
from src.scrapers.ms.locales import LocalesScraper
from src.scrapers.ms.m365_buildnumbers import _SOURCE_URL as M365_URL
from src.scrapers.ms.m365_buildnumbers import M365BuildNumbersScraper
from src.scrapers.ms.win_lifecycle_client import _SOURCES as LC_SOURCES
from src.scrapers.ms.win_lifecycle_client import WinLifecycleClientScraper
from src.scrapers.ms.win_lifecycle_ltsc import _SOURCE_URL as LTSC_URL
from src.scrapers.ms.win_lifecycle_ltsc import WinLifecycleLtscScraper
from src.scrapers.ms.win_lifecycle_server import _SOURCES as LS_SOURCES
from src.scrapers.ms.win_lifecycle_server import WinLifecycleServerScraper
from src.scrapers.ms.win_releases import _WIN10_URL, _WIN11_URL, WinReleasesScraper
from src.scrapers.ms.win_sku import _SOURCE_URL as SKU_URL
from src.scrapers.ms.win_sku import WinSkuScraper

F = Path(__file__).parent / "fixtures" / "ms"

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def win_releases_pages():
    return {
        _WIN10_URL: (F / "win_release_info.html").read_text(),
        _WIN11_URL: (F / "win11_release_info.html").read_text(),
    }


@pytest.fixture(scope="module")
def lifecycle_client_pages():
    names = [
        "win10_lifecycle_enterprise.html",
        "win11_lifecycle_enterprise.html",
        "win10_lifecycle_home_pro.html",
        "win11_lifecycle_home_pro.html",
    ]
    return {url: (F / name).read_text() for url, name in zip(LC_SOURCES, names, strict=True)}


@pytest.fixture(scope="module")
def lifecycle_ltsc_pages():
    return {LTSC_URL: (F / "win_release_info.html").read_text()}


@pytest.fixture(scope="module")
def lifecycle_server_pages():
    server_fixtures = {
        LS_SOURCES[0]: "server2008_lifecycle.html",
        LS_SOURCES[1]: "server2008r2_lifecycle.html",
        LS_SOURCES[2]: "server2012_lifecycle.html",
        LS_SOURCES[3]: "server2012r2_lifecycle.html",
        LS_SOURCES[4]: "server2016_lifecycle.html",
        LS_SOURCES[5]: "server2019_lifecycle.html",
        LS_SOURCES[6]: "server2022_lifecycle.html",
        LS_SOURCES[7]: "server2025_lifecycle.html",
    }
    return {url: (F / fname).read_text() for url, fname in server_fixtures.items()}


# ---------------------------------------------------------------------------
# WinReleasesScraper
# ---------------------------------------------------------------------------

class TestWinReleasesScraper:
    def test_returns_records(self, win_releases_pages):
        records = WinReleasesScraper().parse(win_releases_pages)
        assert len(records) >= 10

    def test_record_keys(self, win_releases_pages):
        records = WinReleasesScraper().parse(win_releases_pages)
        assert set(records[0].keys()) == {"os_type", "major_version", "windows_version", "os_build", "full_version"}

    def test_full_version_prefix(self, win_releases_pages):
        for r in WinReleasesScraper().parse(win_releases_pages):
            assert r["full_version"].startswith("10.0.")

    def test_os_build_matches_full_version(self, win_releases_pages):
        for r in WinReleasesScraper().parse(win_releases_pages):
            assert r["full_version"] == f"10.0.{r['os_build']}"

    def test_os_type_client(self, win_releases_pages):
        for r in WinReleasesScraper().parse(win_releases_pages):
            assert r["os_type"] == "client"

    def test_major_versions_present(self, win_releases_pages):
        records = WinReleasesScraper().parse(win_releases_pages)
        majors = {r["major_version"] for r in records}
        assert 10 in majors
        assert 11 in majors

    def test_no_duplicates(self, win_releases_pages):
        records = WinReleasesScraper().parse(win_releases_pages)
        builds = [r["os_build"] for r in records]
        assert len(builds) == len(set(builds))

    def test_sorted_by_os_build(self, win_releases_pages):
        records = WinReleasesScraper().parse(win_releases_pages)
        builds = [r["os_build"] for r in records]
        assert builds == sorted(builds)


# ---------------------------------------------------------------------------
# WinLifecycleClientScraper
# ---------------------------------------------------------------------------

class TestWinLifecycleClientScraper:
    def test_returns_records(self, lifecycle_client_pages):
        records = WinLifecycleClientScraper().parse(lifecycle_client_pages)
        assert len(records) >= 10

    def test_record_keys(self, lifecycle_client_pages):
        records = WinLifecycleClientScraper().parse(lifecycle_client_pages)
        assert set(records[0].keys()) == {"version", "sku", "start_date", "end_date"}

    def test_dates_are_iso(self, lifecycle_client_pages):
        for r in WinLifecycleClientScraper().parse(lifecycle_client_pages):
            assert DATE_RE.match(r["start_date"]), f"Bad start_date: {r['start_date']}"
            assert DATE_RE.match(r["end_date"]), f"Bad end_date: {r['end_date']}"

    def test_skus_present(self, lifecycle_client_pages):
        skus = {r["sku"] for r in WinLifecycleClientScraper().parse(lifecycle_client_pages)}
        assert any("Windows 10" in s for s in skus)
        assert any("Windows 11" in s for s in skus)

    def test_no_duplicates(self, lifecycle_client_pages):
        records = WinLifecycleClientScraper().parse(lifecycle_client_pages)
        keys = [(r["version"], r["sku"]) for r in records]
        assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# WinLifecycleLtscScraper
# ---------------------------------------------------------------------------

class TestWinLifecycleLtscScraper:
    def test_returns_records(self, lifecycle_ltsc_pages):
        records = WinLifecycleLtscScraper().parse(lifecycle_ltsc_pages)
        assert len(records) >= 3

    def test_record_keys(self, lifecycle_ltsc_pages):
        records = WinLifecycleLtscScraper().parse(lifecycle_ltsc_pages)
        assert set(records[0].keys()) == {
            "version", "servicing_option", "build", "start_date",
            "mainstream_end_date", "extended_end_date",
        }

    def test_versions_include_ltsc(self, lifecycle_ltsc_pages):
        records = WinLifecycleLtscScraper().parse(lifecycle_ltsc_pages)
        options = {r["servicing_option"] for r in records}
        assert any("Long-Term Servicing" in o for o in options)

    def test_builds_are_numeric(self, lifecycle_ltsc_pages):
        for r in WinLifecycleLtscScraper().parse(lifecycle_ltsc_pages):
            assert r["build"].isdigit(), f"Non-numeric build: {r['build']}"

    def test_no_duplicates(self, lifecycle_ltsc_pages):
        records = WinLifecycleLtscScraper().parse(lifecycle_ltsc_pages)
        versions = [r["version"] for r in records]
        assert len(versions) == len(set(versions))


# ---------------------------------------------------------------------------
# WinLifecycleServerScraper
# ---------------------------------------------------------------------------

class TestWinLifecycleServerScraper:
    def test_returns_records(self, lifecycle_server_pages):
        records = WinLifecycleServerScraper().parse(lifecycle_server_pages)
        assert len(records) >= 8

    def test_record_keys(self, lifecycle_server_pages):
        records = WinLifecycleServerScraper().parse(lifecycle_server_pages)
        assert set(records[0].keys()) == {
            "version", "tier", "start_date", "mainstream_end_date", "extended_end_date",
        }

    def test_dates_are_iso(self, lifecycle_server_pages):
        for r in WinLifecycleServerScraper().parse(lifecycle_server_pages):
            assert DATE_RE.match(r["start_date"]), f"Bad start_date: {r['start_date']}"
            assert DATE_RE.match(r["mainstream_end_date"])
            assert DATE_RE.match(r["extended_end_date"])

    def test_covers_all_server_versions(self, lifecycle_server_pages):
        versions = {r["version"] for r in WinLifecycleServerScraper().parse(lifecycle_server_pages)}
        for year in ("2008", "2012", "2016", "2019", "2022", "2025"):
            assert any(year in v for v in versions), f"Missing Server {year}"


# ---------------------------------------------------------------------------
# WinSkuScraper
# ---------------------------------------------------------------------------

class TestWinSkuScraper:
    def test_returns_records(self):
        records = WinSkuScraper().parse({SKU_URL: (F / "win_sku.html").read_text()})
        assert len(records) >= 50

    def test_record_keys(self):
        records = WinSkuScraper().parse({SKU_URL: (F / "win_sku.html").read_text()})
        assert set(records[0].keys()) == {"value", "hex", "dec", "meaning"}

    def test_values_start_with_product(self):
        for r in WinSkuScraper().parse({SKU_URL: (F / "win_sku.html").read_text()}):
            assert r["value"].startswith("PRODUCT_")

    def test_dec_matches_hex(self):
        for r in WinSkuScraper().parse({SKU_URL: (F / "win_sku.html").read_text()}):
            assert int(r["hex"], 16) == r["dec"], f"Mismatch: {r['hex']} != {r['dec']}"

    def test_sorted_by_dec(self):
        records = WinSkuScraper().parse({SKU_URL: (F / "win_sku.html").read_text()})
        dec_values = [r["dec"] for r in records]
        assert dec_values == sorted(dec_values)


# ---------------------------------------------------------------------------
# M365BuildNumbersScraper
# ---------------------------------------------------------------------------

class TestM365BuildNumbersScraper:
    def test_returns_records(self):
        records = M365BuildNumbersScraper().parse({M365_URL: (F / "m365_update_history.html").read_text()})
        assert len(records) >= 100

    def test_record_keys(self):
        records = M365BuildNumbersScraper().parse({M365_URL: (F / "m365_update_history.html").read_text()})
        assert set(records[0].keys()) == {"release_date", "channel", "build", "version", "full_build"}

    def test_channels_present(self):
        records = M365BuildNumbersScraper().parse({M365_URL: (F / "m365_update_history.html").read_text()})
        channels = {r["channel"] for r in records}
        assert "Current" in channels
        assert "Monthly Enterprise" in channels

    def test_full_build_prefix(self):
        for r in M365BuildNumbersScraper().parse({M365_URL: (F / "m365_update_history.html").read_text()}):
            assert r["full_build"].startswith("16.0.")
            assert r["full_build"] == f"16.0.{r['build']}"

    def test_dates_are_iso(self):
        for r in M365BuildNumbersScraper().parse({M365_URL: (F / "m365_update_history.html").read_text()}):
            assert DATE_RE.match(r["release_date"]), f"Bad date: {r['release_date']}"

    def test_sorted_descending_by_date(self):
        records = M365BuildNumbersScraper().parse({M365_URL: (F / "m365_update_history.html").read_text()})
        dates = [r["release_date"] for r in records]
        assert dates == sorted(dates, reverse=True)


# ---------------------------------------------------------------------------
# AsrGuidsScraper
# ---------------------------------------------------------------------------

class TestAsrGuidsScraper:
    def test_returns_records(self):
        records = AsrGuidsScraper().parse({ASR_URL: (F / "asr_guids.html").read_text()})
        assert len(records) >= 10

    def test_record_keys(self):
        records = AsrGuidsScraper().parse({ASR_URL: (F / "asr_guids.html").read_text()})
        assert set(records[0].keys()) == {"asr_name", "asr_guid"}

    def test_guids_are_valid_uuids(self):
        for r in AsrGuidsScraper().parse({ASR_URL: (F / "asr_guids.html").read_text()}):
            assert UUID_RE.fullmatch(r["asr_guid"]), f"Invalid UUID: {r['asr_guid']}"

    def test_guids_are_lowercase(self):
        for r in AsrGuidsScraper().parse({ASR_URL: (F / "asr_guids.html").read_text()}):
            assert r["asr_guid"] == r["asr_guid"].lower()

    def test_no_duplicates(self):
        records = AsrGuidsScraper().parse({ASR_URL: (F / "asr_guids.html").read_text()})
        guids = [r["asr_guid"] for r in records]
        assert len(guids) == len(set(guids))


# ---------------------------------------------------------------------------
# ChassisTypesScraper
# ---------------------------------------------------------------------------

class TestChassisTypesScraper:
    def test_returns_records(self):
        records = ChassisTypesScraper().parse({CHASSIS_URL: (F / "chassis_types.html").read_text()})
        assert len(records) >= 20

    def test_record_keys(self):
        records = ChassisTypesScraper().parse({CHASSIS_URL: (F / "chassis_types.html").read_text()})
        assert set(records[0].keys()) == {"value", "number"}

    def test_numbers_are_positive_ints(self):
        for r in ChassisTypesScraper().parse({CHASSIS_URL: (F / "chassis_types.html").read_text()}):
            assert isinstance(r["number"], int) and r["number"] > 0

    def test_sorted_by_number(self):
        records = ChassisTypesScraper().parse({CHASSIS_URL: (F / "chassis_types.html").read_text()})
        nums = [r["number"] for r in records]
        assert nums == sorted(nums)

    def test_common_types_present(self):
        values = {r["value"] for r in ChassisTypesScraper().parse({CHASSIS_URL: (F / "chassis_types.html").read_text()})}
        assert "Notebook" in values or any("notebook" in v.lower() for v in values)


# ---------------------------------------------------------------------------
# LocalesScraper
# ---------------------------------------------------------------------------

class TestLocalesScraper:
    def test_returns_records(self):
        records = LocalesScraper().parse({LOCALES_URL: (F / "ms_locales.html").read_text()})
        assert len(records) >= 100

    def test_record_keys(self):
        records = LocalesScraper().parse({LOCALES_URL: (F / "ms_locales.html").read_text()})
        assert set(records[0].keys()) == {"lang_code", "lang_code_hex", "lang_name", "lang_tag"}

    def test_en_us_present(self):
        records = LocalesScraper().parse({LOCALES_URL: (F / "ms_locales.html").read_text()})
        en_us = [r for r in records if r["lang_tag"] == "en-US"]
        assert len(en_us) == 1
        assert en_us[0]["lang_code"] == 1033
        assert en_us[0]["lang_code_hex"] == "0409"

    def test_hex_matches_decimal(self):
        for r in LocalesScraper().parse({LOCALES_URL: (F / "ms_locales.html").read_text()}):
            assert int(r["lang_code_hex"], 16) == r["lang_code"]

    def test_sorted_by_lang_code(self):
        records = LocalesScraper().parse({LOCALES_URL: (F / "ms_locales.html").read_text()})
        codes = [r["lang_code"] for r in records]
        assert codes == sorted(codes)


# ---------------------------------------------------------------------------
# BitlockerVolumeTypesScraper
# ---------------------------------------------------------------------------

class TestBitlockerVolumeTypesScraper:
    def test_returns_records(self):
        records = BitlockerVolumeTypesScraper().parse({BL_URL: (F / "bitlocker_recovery_key.html").read_text()})
        assert len(records) >= 2

    def test_record_keys(self):
        records = BitlockerVolumeTypesScraper().parse({BL_URL: (F / "bitlocker_recovery_key.html").read_text()})
        assert set(records[0].keys()) == {"volume_type_enum", "description"}

    def test_os_volume_present(self):
        records = BitlockerVolumeTypesScraper().parse({BL_URL: (F / "bitlocker_recovery_key.html").read_text()})
        descriptions = {r["description"] for r in records}
        assert "operatingSystemVolume" in descriptions

    def test_sorted_by_enum(self):
        records = BitlockerVolumeTypesScraper().parse({BL_URL: (F / "bitlocker_recovery_key.html").read_text()})
        enums = [r["volume_type_enum"] for r in records]
        assert enums == sorted(enums)


# ---------------------------------------------------------------------------
# ValueError guard tests (empty / malformed HTML)
# ---------------------------------------------------------------------------

_EMPTY = "<html><body></body></html>"


class TestValueErrorGuards:
    def test_win_releases_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            WinReleasesScraper().parse({_WIN10_URL: _EMPTY, _WIN11_URL: _EMPTY})

    def test_win_lifecycle_client_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            WinLifecycleClientScraper().parse({url: _EMPTY for url in LC_SOURCES})

    def test_win_lifecycle_ltsc_raises_on_missing_table(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            WinLifecycleLtscScraper().parse({LTSC_URL: _EMPTY})

    def test_win_lifecycle_server_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            WinLifecycleServerScraper().parse({url: _EMPTY for url in LS_SOURCES})

    def test_win_sku_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            WinSkuScraper().parse({SKU_URL: _EMPTY})

    def test_m365_raises_on_too_few_tables(self):
        html = "<html><body><table><tr><td>only one table</td></tr></table></body></html>"
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            M365BuildNumbersScraper().parse({M365_URL: html})

    def test_asr_guids_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            AsrGuidsScraper().parse({ASR_URL: _EMPTY})

    def test_chassis_raises_when_boundary_missing(self):
        # No CreationClassName strong element — boundary detection fails
        html = "<html><body><strong>NotTheRight</strong> (1)</body></html>"
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            ChassisTypesScraper().parse({CHASSIS_URL: html})

    def test_chassis_raises_when_boundary_present_but_no_entries(self):
        # Boundary exists but nothing before it matches the number pattern
        html = "<html><body><strong>CreationClassName</strong></body></html>"
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            ChassisTypesScraper().parse({CHASSIS_URL: html})

    def test_locales_raises_on_no_tables(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            LocalesScraper().parse({LOCALES_URL: _EMPTY})

    def test_bitlocker_raises_on_empty(self):
        with pytest.raises(StructureChangedError, match="page structure may have changed"):
            BitlockerVolumeTypesScraper().parse({BL_URL: _EMPTY})
