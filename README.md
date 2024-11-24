# Data For Geeks
This is a forked project from the marvelously-splendid [Data For Nerds](https://datafornerds.io) project with just a few tweaks:
 - Data is *generally* refreshed quickly
 - Some behind-the-scenes workflows are validating newer versions of actions
 - Additional datasets that I build will be available here first for validation

## Available Datasets
### M365 apps
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msapps/buildnumbers.json

Properties: `ReleaseDate`, `Channel`, `Build`, `Version`, `FullVersion`

### Attack Surface Reduction GUIDs
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/msasrguid.json

Properties: `AsrName`, `AsrGuid`

### Chassis Types
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/mschassistypes.json

Properties: `Value`, `Number`

### Locales
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/mslocales.json

Properties: `LangCode`, `LangHex`, `LangName`, `LangTag`

### Windows Builds
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/buildnumbers.json

Properties: `Win10Version`, `Version`, `ReleaseDate`, `Article`, `KBTitle`, `LTSCOnly`, `Comment`

### Client OS Lifecycle Dates
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-client.json

Properties: `Version`, `SKU`, `StartDate`, `EndDate`

### LTSC Client OS Lifecycle Dates
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-client-ltsc.json

Properties: `Version`, `ServicingOption`, `Build`, `StartDate`, `MainstreamEndDate`, `ExtendedEndDate`

### LTSC Server OS Lifecycle Dates
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-server.json

Properties: `Version`, `StartDate`, `MainstreamEndDate`, `ExtendedEndDate`

### Operating System SKUs
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/msoperatingsystemsku.json

Properties: `Value`, `Hex`, `Dec`, `Meaning`

### Windows Releases
https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/releases.json

Properties: `Version`, `FullVersion`, `Build`

## How To Use
### PowerShell
You can consume this data using the `Invoke-RestMethod` command, passing the JSON URL for the `Uri` parameter. For example:

```
$data = Invoke-RestMethod -Uri "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/buildnumbers.json"
```

### PowerBI
You can get this data using the `Web` data source. When prompted for authentication, select Anonymous.