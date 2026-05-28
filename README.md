# DataForGeeks

[![CI](https://github.com/altrhombus/DataForGeeks/actions/workflows/ci.yml/badge.svg)](https://github.com/altrhombus/DataForGeeks/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Machine-readable JSON datasets for Microsoft, Apple, Google, and Linux reference data — Windows build numbers, lifecycle dates, Exchange/SQL/M365 versions, ASR rules, macOS/iOS/Android releases, Ubuntu support dates, and more. All data is scraped directly from public vendor documentation and updated automatically on a regular schedule.

No authentication required. All datasets are served as plain JSON from GitHub's raw content CDN.

---

## Dataset Catalog

| Dataset | Path | Updated |
|---|---|---|
| [Windows OS Build Numbers](#windows-os-build-numbers) | `content/ms/win/buildnumbers.json` | 4× daily |
| [Windows OS Releases](#windows-os-releases) | `content/ms/win/releases.json` | 4× daily |
| [M365 App Build Numbers](#m365-app-build-numbers) | `content/ms/apps/buildnumbers.json` | 4× daily |
| [Windows Client Lifecycle](#windows-client-lifecycle) | `content/ms/win/lifecycle-client.json` | Daily |
| [Windows Client LTSC Lifecycle](#windows-client-ltsc-lifecycle) | `content/ms/win/lifecycle-ltsc.json` | Daily |
| [Windows Server Lifecycle](#windows-server-lifecycle) | `content/ms/win/lifecycle-server.json` | Daily |
| [Microsoft Edge Releases](#microsoft-edge-releases) | `content/ms/other/edge-releases.json` | Weekly |
| [Exchange Server Build Numbers](#exchange-server-build-numbers) | `content/ms/exchange/buildnumbers.json` | Monthly |
| [SQL Server Build Numbers](#sql-server-build-numbers) | `content/ms/sql/buildnumbers.json` | Weekly |
| [.NET Lifecycle](#net-lifecycle) | `content/ms/other/dotnet-lifecycle.json` | Monthly |
| [Attack Surface Reduction GUIDs](#attack-surface-reduction-guids) | `content/ms/other/asr-guids.json` | Monthly |
| [BitLocker Volume Types](#bitlocker-volume-types) | `content/ms/other/bitlocker-volume-types.json` | Monthly |
| [Chassis Types](#chassis-types) | `content/ms/other/chassis-types.json` | Monthly |
| [Locales](#locales) | `content/ms/other/locales.json` | Monthly |
| [Windows OS SKUs](#windows-os-skus) | `content/ms/win/sku.json` | Monthly |
| [macOS Releases](#macos-releases) | `content/apple/macos/releases.json` | Weekly |
| [iOS / iPadOS Releases](#ios--ipados-releases) | `content/apple/ios/releases.json` | Weekly |
| [Android Releases](#android-releases) | `content/google/android/releases.json` | Monthly |
| [Ubuntu Releases](#ubuntu-releases) | `content/linux/ubuntu/releases.json` | Monthly |

Raw URLs follow the pattern:
```
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/<path>
```

---

## Quick Start

### PowerShell

```powershell
$data = Invoke-RestMethod -Uri "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/buildnumbers.json"
$data.data | Where-Object { $_.windows_version -eq "24H2" } | Sort-Object release_date -Descending | Select-Object -First 5
```

### curl + jq

```bash
curl -s https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/releases.json | jq '.data'
```

### Power BI

Use the **Web** connector with the raw URL. When prompted for authentication, select **Anonymous**.

---

## Response Structure

Every dataset follows the same envelope:

```json
{
  "metadata": {
    "provider": "DataForGeeks",
    "apiVersion": "v2",
    "dataset": "windows-update-history",
    "recordCount": 4821,
    "sourceUrls": [
      "https://support.microsoft.com/en-us/topic/..."
    ],
    "lastModified": "2026-05-27T06:00:00Z",
    "lastCollected": "2026-05-27T06:00:00Z"
  },
  "data": [ ... ]
}
```

All dates in `data` records are `yyyy-MM-dd` strings unless otherwise noted. The records you want are always in `data`.

---

## Datasets

### Windows OS Build Numbers

Every cumulative update released for Windows 10, Windows 11, and Windows Server 2016–2025, sourced from the Microsoft support update history pages. Includes hotpatch entries for Server Azure Edition.

**Path:** `content/ms/win/buildnumbers.json`

| Field | Description |
|---|---|
| `full_version` | Full version string (`10.0.22621.5192`) |
| `build` | Build + revision (`22621.5192`) |
| `os_type` | `client`, `server`, or `hotpatch` |
| `major_version` | `10` or `11` for client; server year for server builds |
| `windows_version` | Marketing version (`22H2`) or server product name |
| `release_date` | Date the update was released |
| `kb_article` | KB article number (`KB5058411`) |
| `release_type` | Update type (`Cumulative Update`, `Preview`, etc.) |
| `is_expired` | `true` if the update is no longer in support |
| `article_url` | Link to the KB article |

---

### Windows OS Releases

Major Windows 10 and Windows 11 feature releases — not individual cumulative updates.

**Path:** `content/ms/win/releases.json`

| Field | Description |
|---|---|
| `os_type` | `client` or `server` |
| `major_version` | `10` or `11` |
| `windows_version` | Marketing version name (`22H2`, `23H2`) |
| `os_build` | Base build number (`22621`) |
| `full_version` | Full version string (`10.0.22621`) |

---

### M365 App Build Numbers

Build numbers for Microsoft 365 Apps across all update channels.

**Path:** `content/ms/apps/buildnumbers.json`

| Field | Description |
|---|---|
| `release_date` | Date the build was released |
| `channel` | Update channel (`Current`, `Monthly Enterprise`, `Semi-Annual Enterprise`, etc.) |
| `build` | Short build number (`19929.20164`) |
| `version` | Version number (`2604`) |
| `full_build` | Full build string including major version (`16.0.19929.20164`) |

---

### Windows Client Lifecycle

Mainstream support end dates for Windows 10 and Windows 11 feature releases by SKU.

**Path:** `content/ms/win/lifecycle-client.json`

| Field | Description |
|---|---|
| `version` | Feature release version (`22H2`) |
| `sku` | Windows edition (`Windows 11 Home and Pro`) |
| `start_date` | General availability date |
| `end_date` | End of servicing date |

---

### Windows Client LTSC Lifecycle

Mainstream and extended support dates for Windows Long-Term Servicing Channel (LTSC) and Long-Term Servicing Branch (LTSB) releases.

**Path:** `content/ms/win/lifecycle-ltsc.json`

| Field | Description |
|---|---|
| `version` | LTSC release (`2021 (21H2)`) |
| `servicing_option` | `Long-Term Servicing Channel (LTSC)` or `Long-Term Servicing Branch (LTSB)` |
| `build` | Base build number (`19044`) |
| `start_date` | General availability date |
| `mainstream_end_date` | End of mainstream support — may be the string `"End of updates"` for older LTSB releases where Microsoft does not publish a discrete date |
| `extended_end_date` | End of extended support |

---

### Windows Server Lifecycle

Mainstream and extended support dates for Windows Server 2008 through 2025, including Service Pack and Extended Security Update (ESU) year entries.

**Path:** `content/ms/win/lifecycle-server.json`

| Field | Description |
|---|---|
| `version` | Windows Server OS name (`Windows Server 2019`) |
| `tier` | Support tier within the product (`Service Pack 1`, `Extended Security Update Year 1`) |
| `start_date` | General availability or tier start date |
| `mainstream_end_date` | End of mainstream support |
| `extended_end_date` | End of extended support |

---

### Microsoft Edge Releases

Stable channel releases for Microsoft Edge (Chromium-based).

**Path:** `content/ms/other/edge-releases.json`

| Field | Description |
|---|---|
| `version` | Full version string (`136.0.3240.50`) |
| `major_version` | Major version number (`136`) |
| `release_date` | Date the version was released |

---

### Exchange Server Build Numbers

Build numbers for all Exchange Server versions and cumulative updates.

**Path:** `content/ms/exchange/buildnumbers.json`

| Field | Description |
|---|---|
| `product_name` | Exchange product line (`Exchange Server 2019`) |
| `exchange_version` | Version label (`2019`, `2016`) |
| `build` | Short build number (`15.2.1258.27`) |
| `build_long` | Long build number (`15.02.1258.027`) |
| `release_date` | Date the build was released |

---

### SQL Server Build Numbers

Cumulative updates and service packs for all SQL Server versions.

**Path:** `content/ms/sql/buildnumbers.json`

| Field | Description |
|---|---|
| `sql_version` | SQL Server version label (`SQL Server 2022`) |
| `major_version` | Major version number (`16`) |
| `build` | Build number string |
| `service_pack` | Service pack or cumulative update label |
| `update_type` | Type of update (`CU`, `RTM`, `GDR`) |
| `kb_article` | KB article number |
| `release_date` | Date the build was released |
| `article_url` | Link to the KB article |

---

### .NET Lifecycle

Release and end-of-support dates for .NET Framework and .NET (formerly .NET Core) versions.

**Path:** `content/ms/other/dotnet-lifecycle.json`

| Field | Description |
|---|---|
| `product` | Product name (`.NET Framework 4.8`, `.NET 9`) |
| `version` | Version string |
| `release_date` | General availability date |
| `end_date` | End of support date |

---

### Attack Surface Reduction GUIDs

Rule names and GUIDs for all Microsoft Defender Attack Surface Reduction (ASR) rules.

**Path:** `content/ms/other/asr-guids.json`

| Field | Description |
|---|---|
| `asr_name` | Human-readable rule name |
| `asr_guid` | Rule GUID used in policy configuration |

---

### BitLocker Volume Types

Volume type enum values from the Microsoft Graph `bitlockerRecoveryKey` resource.

**Path:** `content/ms/other/bitlocker-volume-types.json`

| Field | Description |
|---|---|
| `volume_type_enum` | Integer enum value |
| `description` | Volume type name (`operatingSystemVolume`, `fixedDataVolume`) |

---

### Chassis Types

The `Win32_SystemEnclosure` chassis type enumeration from the WMI CIM schema. Useful for interpreting `ChassisTypes` returned by `Get-CimInstance Win32_SystemEnclosure`.

**Path:** `content/ms/other/chassis-types.json`

| Field | Description |
|---|---|
| `value` | Chassis type name (`Notebook`, `Desktop`) |
| `number` | Integer value returned by WMI |

---

### Locales

Windows locale identifiers from the MS-OE376 Office Open XML specification, including decimal code, hex code, language name, and IETF language tag.

**Path:** `content/ms/other/locales.json`

| Field | Description |
|---|---|
| `lang_code` | Decimal locale identifier (LCID) |
| `lang_code_hex` | Hex locale identifier (`0409`) |
| `lang_name` | Locale display name (`English - United States`) |
| `lang_tag` | IETF BCP 47 language tag (`en-US`) |

---

### Windows OS SKUs

The `GetProductInfo` API enumeration — integer and hex SKU codes returned by `(Get-CimInstance Win32_OperatingSystem).OperatingSystemSKU` and related APIs.

**Path:** `content/ms/win/sku.json`

| Field | Description |
|---|---|
| `value` | API constant name (`PRODUCT_PROFESSIONAL`) |
| `hex` | Hex value (`0x00000030`) |
| `dec` | Decimal integer value |
| `meaning` | Description of the edition |

---

### macOS Releases

All macOS major and minor releases with dates, sourced from Apple's security releases page.

**Path:** `content/apple/macos/releases.json`

| Field | Description |
|---|---|
| `os_name` | macOS version name (`Sequoia`, `Ventura`) |
| `version` | Version number (`15.5`) |
| `major_version` | Major version number (`15`) |
| `release_date` | Date the version was released |

---

### iOS / iPadOS Releases

All iOS and iPadOS major and minor releases with dates, sourced from Apple's security releases page.

**Path:** `content/apple/ios/releases.json`

| Field | Description |
|---|---|
| `product` | Product label (`iOS` or `iPadOS`) |
| `version` | Version number (`18.5`) |
| `major_version` | Major version number (`18`) |
| `release_date` | Date the version was released |

---

### Android Releases

Android platform versions with API levels and initial release dates.

**Path:** `content/google/android/releases.json`

| Field | Description |
|---|---|
| `version` | Android version name (`Android 15`) |
| `api_level` | API level integer or range (`35`) |
| `release_date` | First public release date (normalized to first of month when exact date is unavailable) |

---

### Ubuntu Releases

Ubuntu LTS and standard releases with Canonical support lifecycle dates, sourced from the Launchpad API.

**Path:** `content/linux/ubuntu/releases.json`

| Field | Description |
|---|---|
| `version` | Ubuntu version number (`24.04`) |
| `codename` | Release codename (`Noble Numbat`) |
| `series` | Short series name (`noble`) |
| `release_date` | Release date |
| `status` | Support status (`Active`, `End of Life`) |
| `is_lts` | `true` if this is a Long Term Support release |
| `standard_support_end` | End of standard (free) support |
| `esm_support_end` | End of Extended Security Maintenance, or `null` if not applicable |

---

## How It Works

Each dataset is maintained by a Python scraper that:

1. Fetches HTML or JSON from the vendor's public documentation using `httpx`
2. Parses the page with `BeautifulSoup` — no JavaScript execution, no headless browser
3. Validates and normalizes each record through a `pydantic` model
4. Compares the result against the current file in this repository
5. Writes the updated JSON only if the data has changed

A GitHub Actions workflow runs each scraper on the schedule shown in the catalog. If data has changed, the workflow opens a pull request which is automatically merged. If nothing changed, the run exits cleanly with no PR created.

Scrapers live in `src/scrapers/` and output to `content/`. To run a scraper locally:

```bash
uv sync
uv run python run.py win-buildnumbers
```

Run `uv run python run.py` with no arguments to see all available scraper names.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, how to add a new scraper, and PR expectations.

---

*Forked from [Data For Nerds](https://datafornerds.io) with additional datasets and a full Python rewrite. Licensed under the [MIT License](LICENSE).*
