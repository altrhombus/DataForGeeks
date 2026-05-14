# DataForGeeks

Machine-readable JSON files containing Microsoft reference data — Windows build numbers, lifecycle dates, M365 app versions, ASR rules, OS SKUs, and more. All files are fetched directly from Microsoft's public documentation and updated automatically on a regular schedule.

No authentication required. All data is served as plain JSON from GitHub's raw content CDN.

---

## Dataset Catalog

| Dataset | URL | Updated |
|---|---|---|
| [M365 App Build Numbers](#m365-app-build-numbers) | `content/ms/msapps/buildnumbers.json` | 4× daily |
| [Windows OS Build Numbers](#windows-os-build-numbers) | `content/ms/mswin/buildnumbers.json` | 4× daily |
| [Windows OS Releases](#windows-os-releases) | `content/ms/mswin/releases.json` | 4× daily |
| [Windows Client Lifecycle](#windows-client-lifecycle) | `content/ms/mswin/lifecycle-client.json` | Daily |
| [Windows Client LTSC Lifecycle](#windows-client-ltsc-lifecycle) | `content/ms/mswin/lifecycle-client-ltsc.json` | Daily |
| [Windows Server Lifecycle](#windows-server-lifecycle) | `content/ms/mswin/lifecycle-server.json` | Daily |
| [Attack Surface Reduction GUIDs](#attack-surface-reduction-guids) | `content/ms/msother/msasrguid.json` | Monthly |
| [Chassis Types](#chassis-types) | `content/ms/msother/mschassistypes.json` | Monthly |
| [Locales](#locales) | `content/ms/msother/mslocales.json` | Monthly |
| [Windows OS SKUs](#windows-os-skus) | `content/ms/mswin/msoperatingsystemsku.json` | Monthly |
| [BitLocker Volume Types](#bitlocker-volume-types) | `content/ms/msother/msgraph-bitlockerRecoveryKey.json` | Monthly |

Raw URLs follow the pattern:
```
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/<path>/<file>.json
```

---

## Quick Start

### PowerShell

```powershell
$data = Invoke-RestMethod -Uri "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/buildnumbers.json"
$data.Data | Where-Object { $_.Version -like "22621*" } | Sort-Object ReleaseDate -Descending | Select-Object -First 5
```

### Power BI

Use the **Web** connector with the raw URL above. When prompted for authentication, select **Anonymous**.

### curl

```bash
curl -s https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/releases.json | jq '.Data'
```

---

## Response Structure

Every file follows the same envelope:

```json
{
  "DataForGeeks": {
    "LastUpdatedUTC": "2026-05-13T06:00:00Z",
    "SourceList": [ "https://..." ]
  },
  "Data": [ ... ]
}
```

`LastUpdatedUTC` reflects the last time the file was written. `SourceList` lists the Microsoft documentation pages the data was scraped from. The data you want is always in `Data`.

---

## Datasets

### M365 App Build Numbers

Build numbers for Microsoft 365 Apps (formerly Office 365) across all update channels, sourced from the Microsoft 365 Apps update history page.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msapps/buildnumbers.json`

| Field | Description |
|---|---|
| `ReleaseDate` | Date the build was released (`yyyy-MM-dd`) |
| `Channel` | Update channel (e.g. `Current`, `Monthly Enterprise`, `Semi-Annual Enterprise`) |
| `Build` | Short build number (e.g. `19929.20164`) |
| `Version` | Version number (e.g. `2604`) |
| `FullBuild` | Full build string including major version (e.g. `16.0.19929.20164`) |

---

### Windows OS Build Numbers

Every cumulative update released for Windows 10, Windows 11, and Windows Server 2022, sourced from the Microsoft support update history pages.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/buildnumbers.json`

| Field | Description |
|---|---|
| `Win10Version` | Full version string in `10.0.xxxxx.xxxxx` format |
| `Version` | Build number and revision (e.g. `22621.5192`) |
| `ReleaseDate` | Date the update was released (`yyyy-MM-dd`) |
| `Article` | KB article number (e.g. `KB5058411`) |
| `KBTitle` | Full KB article title |
| `LTSCOnly` | `true` if the update applies only to LTSC editions |
| `Comment` | Additional notes from the source page, if any |

---

### Windows OS Releases

Major Windows 10 and Windows 11 release versions (feature updates), not individual cumulative updates.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/releases.json`

| Field | Description |
|---|---|
| `Version` | Base build number (e.g. `22621`) |
| `FullVersion` | Full version string (e.g. `10.0.22621`) |
| `Build` | Marketing version name (e.g. `22H2`) |

---

### Windows Client Lifecycle

Mainstream support end dates for Windows 10 and Windows 11 feature releases by SKU.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-client.json`

| Field | Description |
|---|---|
| `Version` | Feature release version (e.g. `22H2`) |
| `SKU` | Windows edition (e.g. `Windows 11 Home and Pro`) |
| `StartDate` | General availability date (`yyyy-MM-dd`) |
| `EndDate` | End of servicing date (`yyyy-MM-dd`) |

---

### Windows Client LTSC Lifecycle

Mainstream and extended support dates for Windows Long-Term Servicing Channel (LTSC) and Long-Term Servicing Branch (LTSB) releases.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-client-ltsc.json`

| Field | Description |
|---|---|
| `Version` | LTSC release (e.g. `2021 (21H2)`) |
| `ServicingOption` | `Long-Term Servicing Channel (LTSC)` or `Long-Term Servicing Branch (LTSB)` |
| `Build` | Base build number (e.g. `19044`) |
| `StartDate` | General availability date (`yyyy-MM-dd`) |
| `MainstreamEndDate` | End of mainstream support (`yyyy-MM-dd`) |
| `ExtendedEndDate` | End of extended support (`yyyy-MM-dd`) |

---

### Windows Server Lifecycle

Mainstream and extended support dates for Windows Server 2008 through 2025, including Service Pack and Extended Security Update (ESU) year entries. Each row includes the product name so Service Pack and ESU entries can be associated with their OS.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-server.json`

| Field | Description |
|---|---|
| `Product` | Windows Server OS name (e.g. `Windows Server 2019`) |
| `Version` | Release or support tier (e.g. `Windows Server 2019`, `Service Pack 1`, `Extended Security Update Year 1`) |
| `StartDate` | General availability or tier start date (`yyyy-MM-dd`) |
| `MainstreamEndDate` | End of mainstream support (`yyyy-MM-dd`) |
| `ExtendedEndDate` | End of extended support (`yyyy-MM-dd`) |

---

### Attack Surface Reduction GUIDs

Rule names and GUIDs for all Microsoft Defender Attack Surface Reduction (ASR) rules.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/msasrguid.json`

| Field | Description |
|---|---|
| `AsrName` | Human-readable rule name |
| `AsrGuid` | Rule GUID used in policy configuration |

---

### Chassis Types

The `Win32_SystemEnclosure` chassis type enumeration values from the WMI CIM schema. Useful for interpreting the `ChassisTypes` property returned by `Get-CimInstance Win32_SystemEnclosure`.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/mschassistypes.json`

| Field | Description |
|---|---|
| `Value` | Chassis type name (e.g. `Notebook`, `Desktop`) |
| `Number` | Integer value returned by WMI |

---

### Locales

Windows locale identifiers from the MS-OE376 Office Open XML specification, including decimal code, hex code, language name, and IETF language tag.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/mslocales.json`

| Field | Description |
|---|---|
| `LangCode` | Decimal locale identifier (LCID) |
| `LangCodeHex` | Hex locale identifier (e.g. `0409`) |
| `LangName` | Locale display name (e.g. `English - United States`) |
| `LangTag` | IETF BCP 47 language tag (e.g. `en-US`) |

---

### Windows OS SKUs

The `GetProductInfo` API enumeration — integer and hex SKU codes returned by `(Get-CimInstance Win32_OperatingSystem).OperatingSystemSKU` and related APIs.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/msoperatingsystemsku.json`

| Field | Description |
|---|---|
| `Value` | API constant name (e.g. `PRODUCT_PROFESSIONAL`) |
| `Hex` | Hex value (e.g. `0x00000030`) |
| `Dec` | Decimal integer value |
| `Meaning` | Description of the edition |

---

### BitLocker Volume Types

Volume type enum values from the Microsoft Graph `bitlockerRecoveryKey` resource.

**URL:** `https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/msgraph-bitlockerRecoveryKey.json`

| Field | Description |
|---|---|
| `VolumeTypeEnum` | Integer enum value |
| `Description` | Volume type name (e.g. `operatingSystemVolume`, `fixedDataVolume`) |

---

## How It Works

Each dataset is maintained by a PowerShell script that:

1. Fetches the current JSON from this repository's `main` branch
2. Scrapes the corresponding Microsoft documentation page using `Invoke-WebRequest -UseBasicParsing`
3. Parses the raw HTML — no JavaScript execution, no headless browser
4. Compares the freshly scraped data against the current file
5. Writes the updated JSON locally only if the data has changed

A GitHub Actions workflow runs each script on the schedule shown in the catalog. If data has changed, the workflow opens a pull request which is automatically merged. If nothing changed, the run exits cleanly with no PR created.

Scripts live in `scripts/ms/` and output to `content/ms/`. Workflows are in `.github/workflows/`.

---

*Forked from [Data For Nerds](https://datafornerds.io) with additional datasets and workflow improvements.*
