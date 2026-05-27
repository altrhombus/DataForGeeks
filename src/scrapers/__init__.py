from src.scrapers.apple.ios_releases import IosReleasesScraper
from src.scrapers.apple.macos_releases import MacOsReleasesScraper
from src.scrapers.google.android_releases import AndroidReleasesScraper
from src.scrapers.linux.ubuntu_releases import UbuntuReleasesScraper
from src.scrapers.ms.asr_guids import AsrGuidsScraper
from src.scrapers.ms.bitlocker_volume_types import BitlockerVolumeTypesScraper
from src.scrapers.ms.chassis_types import ChassisTypesScraper
from src.scrapers.ms.dotnet_lifecycle import DotnetLifecycleScraper
from src.scrapers.ms.edge_releases import EdgeReleasesScraper
from src.scrapers.ms.exchange_buildnumbers import ExchangeBuildNumbersScraper
from src.scrapers.ms.locales import LocalesScraper
from src.scrapers.ms.m365_buildnumbers import M365BuildNumbersScraper
from src.scrapers.ms.sql_buildnumbers import SqlBuildNumbersScraper
from src.scrapers.ms.win_buildnumbers import WinBuildNumbersScraper
from src.scrapers.ms.win_lifecycle_client import WinLifecycleClientScraper
from src.scrapers.ms.win_lifecycle_ltsc import WinLifecycleLtscScraper
from src.scrapers.ms.win_lifecycle_server import WinLifecycleServerScraper
from src.scrapers.ms.win_releases import WinReleasesScraper
from src.scrapers.ms.win_sku import WinSkuScraper

REGISTRY: dict[str, type] = {
    "android-releases": AndroidReleasesScraper,
    "asr-guids": AsrGuidsScraper,
    "bitlocker-volume-types": BitlockerVolumeTypesScraper,
    "chassis-types": ChassisTypesScraper,
    "dotnet-lifecycle": DotnetLifecycleScraper,
    "edge-releases": EdgeReleasesScraper,
    "exchange-buildnumbers": ExchangeBuildNumbersScraper,
    "ios-releases": IosReleasesScraper,
    "locales": LocalesScraper,
    "m365-buildnumbers": M365BuildNumbersScraper,
    "macos-releases": MacOsReleasesScraper,
    "sql-buildnumbers": SqlBuildNumbersScraper,
    "ubuntu-releases": UbuntuReleasesScraper,
    "win-buildnumbers": WinBuildNumbersScraper,
    "win-lifecycle-client": WinLifecycleClientScraper,
    "win-lifecycle-ltsc": WinLifecycleLtscScraper,
    "win-lifecycle-server": WinLifecycleServerScraper,
    "win-releases": WinReleasesScraper,
    "win-sku": WinSkuScraper,
}
