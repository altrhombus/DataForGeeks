# Data For Geeks
This is a forked project from the marvelously-splendid [Data For Nerds](https://datafornerds.io) project with just a few tweaks:
 - Data is *generally* refreshed quickly
 - Some behind-the-scenes workflows are validating newer versions of actions
 - Additional datasets that I build will be available here first for validation

## Available Datasets
### 
| Uri | Description |
| ----------- | ----------- |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msapps/buildnumbers.json | Microsoft 365 apps |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/msasrguid.json | Attack Surface Reduction GUIDs |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/mschassistypes.json | CIM Chassis Types |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/mslocales.json | Locales |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/buildnumbers.json | Windows Builds |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-client-ltsc.json | LTSC Client OS Lifecycle Dates |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-server.json| LTSC Server OS Lifecycle Dates |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/msoperatingsystemsku.json | Operating System SKUs |
| https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/releases.json | Windows Releases |


## How To Use
### PowerShell
You can consume this data using the `Invoke-RestMethod` command, passing the JSON URL for the `Uri` parameter. For example:

```
$data = Invoke-RestMethod -Uri "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/buildnumbers.json"
```

### PowerBI
You can get this data using the `Web` data source. When prompted for authentication, select Anonymous.