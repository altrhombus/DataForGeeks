"""Tests for Ubuntu, macOS, iOS/iPadOS, and Android scrapers."""

from datetime import date
from pathlib import Path

import pytest

from src.scrapers.linux.ubuntu_releases import UbuntuReleasesScraper, _API_URL as UBUNTU_URL
from src.scrapers.apple.macos_releases import (
    MacOsReleasesScraper, _SOURCE_URL as MACOS_URL, _ARCHIVE_URL as MACOS_ARCHIVE_URL,
)
from src.scrapers.apple.ios_releases import (
    IosReleasesScraper, _SOURCE_URL as IOS_URL, _ARCHIVE_URL as IOS_ARCHIVE_URL,
)
from src.scrapers.google.android_releases import AndroidReleasesScraper, _SOURCE_URL as ANDROID_URL

FIXTURES = Path(__file__).parent / "fixtures"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ubuntu_json() -> str:
    return (FIXTURES / "linux/ubuntu_releases.json").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def apple_current_html() -> str:
    return (FIXTURES / "apple/apple_security_releases_current.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def apple_archive_html() -> str:
    return (FIXTURES / "apple/apple_security_releases_archive.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def android_html() -> str:
    return (FIXTURES / "google/android_releases.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ubuntu_pages(ubuntu_json) -> dict[str, str]:
    return {UBUNTU_URL: ubuntu_json}


@pytest.fixture(scope="module")
def macos_pages(apple_current_html, apple_archive_html) -> dict[str, str]:
    return {MACOS_URL: apple_current_html, MACOS_ARCHIVE_URL: apple_archive_html}


@pytest.fixture(scope="module")
def ios_pages(apple_current_html, apple_archive_html) -> dict[str, str]:
    return {IOS_URL: apple_current_html, IOS_ARCHIVE_URL: apple_archive_html}


@pytest.fixture(scope="module")
def android_pages(android_html) -> dict[str, str]:
    return {ANDROID_URL: android_html}


# ── Ubuntu releases ───────────────────────────────────────────────────────────

_UBUNTU_KEYS = {"version", "codename", "series", "release_date", "status", "is_lts",
                "standard_support_end", "esm_support_end"}


class TestUbuntuReleases:
    def test_returns_records(self, ubuntu_pages):
        records = UbuntuReleasesScraper().parse(ubuntu_pages)
        assert len(records) > 40

    def test_record_keys(self, ubuntu_pages):
        for r in UbuntuReleasesScraper().parse(ubuntu_pages):
            assert set(r.keys()) == _UBUNTU_KEYS

    def test_lts_releases_present(self, ubuntu_pages):
        records = UbuntuReleasesScraper().parse(ubuntu_pages)
        versions = {r["version"] for r in records}
        for lts in ("20.04", "22.04", "24.04"):
            assert lts in versions

    def test_lts_flag_correct(self, ubuntu_pages):
        records = UbuntuReleasesScraper().parse(ubuntu_pages)
        by_version = {r["version"]: r for r in records}
        assert by_version["22.04"]["is_lts"] is True
        assert by_version["21.10"]["is_lts"] is False

    def test_esm_end_null_for_non_lts(self, ubuntu_pages):
        records = UbuntuReleasesScraper().parse(ubuntu_pages)
        for r in records:
            if not r["is_lts"]:
                assert r["esm_support_end"] is None

    def test_esm_end_set_for_lts(self, ubuntu_pages):
        records = UbuntuReleasesScraper().parse(ubuntu_pages)
        for r in records:
            if r["is_lts"]:
                assert r["esm_support_end"] is not None
                date.fromisoformat(r["esm_support_end"])

    def test_release_date_format(self, ubuntu_pages):
        for r in UbuntuReleasesScraper().parse(ubuntu_pages):
            date.fromisoformat(r["release_date"])

    def test_support_end_date_format(self, ubuntu_pages):
        for r in UbuntuReleasesScraper().parse(ubuntu_pages):
            date.fromisoformat(r["standard_support_end"])

    def test_no_duplicates(self, ubuntu_pages):
        records = UbuntuReleasesScraper().parse(ubuntu_pages)
        keys = [r["version"] for r in records]
        assert len(keys) == len(set(keys))

    def test_dataset_slug(self):
        assert UbuntuReleasesScraper.dataset == "linux/ubuntu/releases"

    def test_sources_count(self):
        assert len(UbuntuReleasesScraper.sources) == 1


# ── macOS releases ────────────────────────────────────────────────────────────

_MACOS_KEYS = {"os_name", "version", "major_version", "release_date"}


class TestMacOsReleases:
    def test_returns_records(self, macos_pages):
        records = MacOsReleasesScraper().parse(macos_pages)
        assert len(records) > 50

    def test_record_keys(self, macos_pages):
        for r in MacOsReleasesScraper().parse(macos_pages):
            assert set(r.keys()) == _MACOS_KEYS

    def test_versions_present(self, macos_pages):
        records = MacOsReleasesScraper().parse(macos_pages)
        names = {r["os_name"] for r in records}
        assert "Sonoma" in names
        assert "Sequoia" in names

    def test_major_version_matches_version(self, macos_pages):
        for r in MacOsReleasesScraper().parse(macos_pages):
            assert r["major_version"] == int(r["version"].split(".")[0])

    def test_release_date_format(self, macos_pages):
        for r in MacOsReleasesScraper().parse(macos_pages):
            date.fromisoformat(r["release_date"])

    def test_no_duplicates(self, macos_pages):
        records = MacOsReleasesScraper().parse(macos_pages)
        keys = [(r["version"], r["release_date"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_dataset_slug(self):
        assert MacOsReleasesScraper.dataset == "apple/macos/releases"

    def test_sources_count(self):
        assert len(MacOsReleasesScraper.sources) == 2


# ── iOS/iPadOS releases ───────────────────────────────────────────────────────

_IOS_KEYS = {"product", "version", "major_version", "release_date"}


class TestIosReleases:
    def test_returns_records(self, ios_pages):
        records = IosReleasesScraper().parse(ios_pages)
        assert len(records) > 50

    def test_record_keys(self, ios_pages):
        for r in IosReleasesScraper().parse(ios_pages):
            assert set(r.keys()) == _IOS_KEYS

    def test_both_products_present(self, ios_pages):
        records = IosReleasesScraper().parse(ios_pages)
        products = {r["product"] for r in records}
        assert "iOS" in products
        assert "iPadOS" in products

    def test_major_version_matches_version(self, ios_pages):
        for r in IosReleasesScraper().parse(ios_pages):
            assert r["major_version"] == int(r["version"].split(".")[0])

    def test_release_date_format(self, ios_pages):
        for r in IosReleasesScraper().parse(ios_pages):
            date.fromisoformat(r["release_date"])

    def test_no_duplicates(self, ios_pages):
        records = IosReleasesScraper().parse(ios_pages)
        keys = [(r["product"], r["version"], r["release_date"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_dataset_slug(self):
        assert IosReleasesScraper.dataset == "apple/ios/releases"

    def test_sources_count(self):
        assert len(IosReleasesScraper.sources) == 2


# ── Android releases ──────────────────────────────────────────────────────────

_ANDROID_KEYS = {"version", "api_level", "release_date"}


class TestAndroidReleases:
    def test_returns_records(self, android_pages):
        records = AndroidReleasesScraper().parse(android_pages)
        assert len(records) > 20

    def test_record_keys(self, android_pages):
        for r in AndroidReleasesScraper().parse(android_pages):
            assert set(r.keys()) == _ANDROID_KEYS

    def test_api_levels_present(self, android_pages):
        records = AndroidReleasesScraper().parse(android_pages)
        api_levels = {r["api_level"] for r in records}
        assert 35 in api_levels  # Android 15
        assert 34 in api_levels  # Android 14
        assert 33 in api_levels  # Android 13

    def test_android_12l_present(self, android_pages):
        records = AndroidReleasesScraper().parse(android_pages)
        api_levels = {r["api_level"] for r in records}
        assert 32 in api_levels  # Android 12L
        assert 31 in api_levels  # Android 12

    def test_release_date_format(self, android_pages):
        for r in AndroidReleasesScraper().parse(android_pages):
            date.fromisoformat(r["release_date"])

    def test_no_duplicates(self, android_pages):
        records = AndroidReleasesScraper().parse(android_pages)
        keys = [(r["version"], r["api_level"]) for r in records]
        assert len(keys) == len(set(keys))

    def test_sorted_descending_by_api(self, android_pages):
        records = AndroidReleasesScraper().parse(android_pages)
        api_levels = [r["api_level"] for r in records]
        assert api_levels == sorted(api_levels, reverse=True)

    def test_dataset_slug(self):
        assert AndroidReleasesScraper.dataset == "google/android/releases"

    def test_sources_count(self):
        assert len(AndroidReleasesScraper.sources) == 1
