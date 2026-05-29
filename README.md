# DataForGeeks

[![CI](https://github.com/altrhombus/DataForGeeks/actions/workflows/ci.yml/badge.svg)](https://github.com/altrhombus/DataForGeeks/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

19 machine-readable JSON datasets for IT professionals and developers — Windows build numbers, patch dates, lifecycle deadlines, Exchange/SQL/M365 versions, macOS/iOS/Android releases, Ubuntu support schedules, ASR rules, and more. Scraped directly from vendor documentation, updated automatically via GitHub Actions, and served as plain JSON from GitHub's CDN.

---

## Datasets

All raw URLs follow the pattern:

```
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/<path>
```

### Microsoft — Windows

| Dataset | Docs | JSON | Updated |
|---|---|---|---|
| Windows OS Build Numbers | [↓ docs](#windows-os-build-numbers) | [buildnumbers.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/buildnumbers.json) | 4× daily |
| Windows OS Releases | [↓ docs](#windows-os-releases) | [releases.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/releases.json) | 4× daily |
| Windows Client Lifecycle | [↓ docs](#windows-client-lifecycle) | [lifecycle-client.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/lifecycle-client.json) | Daily |
| Windows Client LTSC Lifecycle | [↓ docs](#windows-client-ltsc-lifecycle) | [lifecycle-ltsc.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/lifecycle-ltsc.json) | Daily |
| Windows Server Lifecycle | [↓ docs](#windows-server-lifecycle) | [lifecycle-server.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/lifecycle-server.json) | Daily |
| Windows OS SKUs | [↓ docs](#windows-os-skus) | [sku.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/sku.json) | Monthly |

### Microsoft — Apps & Services

| Dataset | Docs | JSON | Updated |
|---|---|---|---|
| M365 App Build Numbers | [↓ docs](#m365-app-build-numbers) | [buildnumbers.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/apps/buildnumbers.json) | 4× daily |
| Microsoft Edge Releases | [↓ docs](#microsoft-edge-releases) | [edge-releases.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/edge-releases.json) | Weekly |
| Exchange Server Build Numbers | [↓ docs](#exchange-server-build-numbers) | [buildnumbers.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/exchange/buildnumbers.json) | Monthly |
| SQL Server Build Numbers | [↓ docs](#sql-server-build-numbers) | [buildnumbers.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/sql/buildnumbers.json) | Weekly |
| .NET Lifecycle | [↓ docs](#net-lifecycle) | [dotnet-lifecycle.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/dotnet-lifecycle.json) | Monthly |

### Microsoft — Reference

| Dataset | Docs | JSON | Updated |
|---|---|---|---|
| Attack Surface Reduction GUIDs | [↓ docs](#attack-surface-reduction-guids) | [asr-guids.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/asr-guids.json) | Monthly |
| BitLocker Volume Types | [↓ docs](#bitlocker-volume-types) | [bitlocker-volume-types.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/bitlocker-volume-types.json) | Monthly |
| Chassis Types | [↓ docs](#chassis-types) | [chassis-types.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/chassis-types.json) | Monthly |
| Locales | [↓ docs](#locales) | [locales.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/locales.json) | Monthly |

### Apple

| Dataset | Docs | JSON | Updated |
|---|---|---|---|
| macOS Releases | [↓ docs](#macos-releases) | [releases.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/apple/macos/releases.json) | Weekly |
| iOS / iPadOS Releases | [↓ docs](#ios--ipados-releases) | [releases.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/apple/ios/releases.json) | Weekly |

### Google

| Dataset | Docs | JSON | Updated |
|---|---|---|---|
| Android Releases | [↓ docs](#android-releases) | [releases.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/google/android/releases.json) | Monthly |

### Linux

| Dataset | Docs | JSON | Updated |
|---|---|---|---|
| Ubuntu Releases | [↓ docs](#ubuntu-releases) | [releases.json](https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/linux/ubuntu/releases.json) | Monthly |

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

### Python

```python
import httpx
data = httpx.get("https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/buildnumbers.json").json()
records = data["data"]
```

### Power BI

Use the **Web** connector with the raw URL. When prompted for authentication, select **Anonymous**.

---

## Response Format

Every dataset uses the same envelope:

```json
{
  "metadata": {
    "provider": "DataForGeeks",
    "apiVersion": "v2",
    "dataset": "windows-build-numbers",
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

The records you want are always in `data`. All dates in `data` records are `yyyy-MM-dd` strings unless otherwise noted.

---

## Dataset Reference

### Windows OS Build Numbers

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/buildnumbers.json`

Every cumulative update released for Windows 10, Windows 11, and Windows Server 2016–2025, sourced from the Microsoft support update history pages. Includes hotpatch entries for Server Azure Edition.

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

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/releases.json`

Major Windows 10 and Windows 11 feature releases — not individual cumulative updates.

| Field | Description |
|---|---|
| `os_type` | `client` or `server` |
| `major_version` | `10` or `11` |
| `windows_version` | Marketing version name (`22H2`, `23H2`) |
| `os_build` | Base build number (`22621`) |
| `full_version` | Full version string (`10.0.22621`) |

---

### Windows Client Lifecycle

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/lifecycle-client.json`

Mainstream support end dates for Windows 10 and Windows 11 feature releases by SKU.

| Field | Description |
|---|---|
| `version` | Feature release version (`22H2`) |
| `sku` | Windows edition (`Windows 11 Home and Pro`) |
| `start_date` | General availability date |
| `end_date` | End of servicing date |

---

### Windows Client LTSC Lifecycle

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/lifecycle-ltsc.json`

Mainstream and extended support dates for Windows Long-Term Servicing Channel (LTSC) and Long-Term Servicing Branch (LTSB) releases.

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

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/lifecycle-server.json`

Mainstream and extended support dates for Windows Server 2008 through 2025, including Service Pack and Extended Security Update (ESU) year entries.

| Field | Description |
|---|---|
| `version` | Windows Server OS name (`Windows Server 2019`) |
| `tier` | Support tier within the product (`Service Pack 1`, `Extended Security Update Year 1`) |
| `start_date` | General availability or tier start date |
| `mainstream_end_date` | End of mainstream support |
| `extended_end_date` | End of extended support |

---

### Windows OS SKUs

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/win/sku.json`

The `GetProductInfo` API enumeration — integer and hex SKU codes returned by `(Get-CimInstance Win32_OperatingSystem).OperatingSystemSKU` and related APIs.

| Field | Description |
|---|---|
| `value` | API constant name (`PRODUCT_PROFESSIONAL`) |
| `hex` | Hex value (`0x00000030`) |
| `dec` | Decimal integer value |
| `meaning` | Description of the edition |

---

### M365 App Build Numbers

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/apps/buildnumbers.json`

Build numbers for Microsoft 365 Apps across all update channels.

| Field | Description |
|---|---|
| `release_date` | Date the build was released |
| `channel` | Update channel (`Current`, `Monthly Enterprise`, `Semi-Annual Enterprise`, etc.) |
| `build` | Short build number (`19929.20164`) |
| `version` | Version number (`2604`) |
| `full_build` | Full build string including major version (`16.0.19929.20164`) |

---

### Microsoft Edge Releases

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/edge-releases.json`

Stable channel releases for Microsoft Edge (Chromium-based).

| Field | Description |
|---|---|
| `version` | Full version string (`136.0.3240.50`) |
| `major_version` | Major version number (`136`) |
| `release_date` | Date the version was released |

---

### Exchange Server Build Numbers

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/exchange/buildnumbers.json`

Build numbers for all Exchange Server versions and cumulative updates.

| Field | Description |
|---|---|
| `product_name` | Exchange product line (`Exchange Server 2019`) |
| `exchange_version` | Version label (`2019`, `2016`) |
| `build` | Short build number (`15.2.1258.27`) |
| `build_long` | Long build number (`15.02.1258.027`) |
| `release_date` | Date the build was released |

---

### SQL Server Build Numbers

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/sql/buildnumbers.json`

Cumulative updates and service packs for all SQL Server versions.

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

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/dotnet-lifecycle.json`

Release and end-of-support dates for .NET Framework and .NET (formerly .NET Core) versions.

| Field | Description |
|---|---|
| `product` | Product name (`.NET Framework 4.8`, `.NET 9`) |
| `version` | Version string |
| `release_date` | General availability date |
| `end_date` | End of support date |

---

### Attack Surface Reduction GUIDs

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/asr-guids.json`

Rule names and GUIDs for all Microsoft Defender Attack Surface Reduction (ASR) rules.

| Field | Description |
|---|---|
| `asr_name` | Human-readable rule name |
| `asr_guid` | Rule GUID used in policy configuration |

---

### BitLocker Volume Types

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/bitlocker-volume-types.json`

Volume type enum values from the Microsoft Graph `bitlockerRecoveryKey` resource.

| Field | Description |
|---|---|
| `volume_type_enum` | Integer enum value |
| `description` | Volume type name (`operatingSystemVolume`, `fixedDataVolume`) |

---

### Chassis Types

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/chassis-types.json`

The `Win32_SystemEnclosure` chassis type enumeration from the WMI CIM schema. Useful for interpreting `ChassisTypes` returned by `Get-CimInstance Win32_SystemEnclosure`.

| Field | Description |
|---|---|
| `value` | Chassis type name (`Notebook`, `Desktop`) |
| `number` | Integer value returned by WMI |

---

### Locales

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/other/locales.json`

Windows locale identifiers from the MS-OE376 Office Open XML specification, including decimal code, hex code, language name, and IETF language tag.

| Field | Description |
|---|---|
| `lang_code` | Decimal locale identifier (LCID) |
| `lang_code_hex` | Hex locale identifier (`0409`) |
| `lang_name` | Locale display name (`English - United States`) |
| `lang_tag` | IETF BCP 47 language tag (`en-US`) |

---

### macOS Releases

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/apple/macos/releases.json`

All macOS major and minor releases with dates, sourced from Apple's security releases page.

| Field | Description |
|---|---|
| `os_name` | macOS version name (`Sequoia`, `Ventura`) |
| `version` | Version number (`15.5`) |
| `major_version` | Major version number (`15`) |
| `release_date` | Date the version was released |

---

### iOS / iPadOS Releases

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/apple/ios/releases.json`

All iOS and iPadOS major and minor releases with dates, sourced from Apple's security releases page.

| Field | Description |
|---|---|
| `product` | Product label (`iOS` or `iPadOS`) |
| `version` | Version number (`18.5`) |
| `major_version` | Major version number (`18`) |
| `release_date` | Date the version was released |

---

### Android Releases

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/google/android/releases.json`

Android platform versions with API levels and initial release dates.

| Field | Description |
|---|---|
| `version` | Android version name (`Android 15`) |
| `api_level` | API level integer or range (`35`) |
| `release_date` | First public release date (normalized to first of month when exact date is unavailable) |

---

### Ubuntu Releases

**Raw URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/linux/ubuntu/releases.json`

Ubuntu LTS and standard releases with Canonical support lifecycle dates, sourced from the Launchpad API.

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

A GitHub Actions workflow runs each scraper on the schedule shown in the catalog. If the data has changed, the workflow opens a pull request which is automatically merged. If nothing changed, the run exits cleanly with no PR created.

Scrapers live in `src/scrapers/` and output to `content/`. To run one locally:

```bash
uv sync
uv run python run.py win-buildnumbers
```

Run `uv run python run.py` with no arguments to list all available scraper names.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, how to add a new scraper, and PR expectations.

---

*Forked from [Data For Nerds](https://datafornerds.io) with additional datasets and a full Python rewrite. Licensed under the [MIT License](LICENSE).*
