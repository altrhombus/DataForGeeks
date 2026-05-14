$sourceUrl = "https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/cim-chassis"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/mschassistypes.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

# The ChassisTypes property appears before CreationClassName alphabetically on the page.
# Split on the CreationClassName heading to isolate just the ChassisTypes section,
# preventing false matches from other numbered enum properties lower on the page.
$sections = $pageData.Content -split '<strong>CreationClassName<\/strong>'
if ($sections.Count -lt 2) {
    Throw "CreationClassName section boundary not found - the page structure may have changed"
}

# Chassis type entries appear as: <strong>Name</strong> (Number)
# [^<]+ prevents matching across tag boundaries (no dotall needed here)
$rxEntry = [regex]::New('<strong>([^<]+)<\/strong>\s*\((\d+)\)')

$releaseList = [System.Collections.ArrayList]::new()
$rxEntry.Matches($sections[0]).ForEach{
    $releaseList.Add([PSCustomObject]@{
        Value  = $_.Groups[1].Value.Trim()
        Number = $_.Groups[2].Value.Trim()
    }) | Out-Null
}

if (-not $releaseList.Count) {
    Throw "No chassis type entries parsed - the page structure may have changed"
}

$releaseList = $releaseList | Sort-Object { [int]$_.Number } | Select-Object Value, Number -Unique

$outputData = [PSCustomObject]@{
    DataForGeeks = [PSCustomObject]@{
        LastUpdatedUTC = (Get-Date).ToUniversalTime()
        SourceList     = @($sourceUrl)
    }
    Data = $releaseList
}

$allProperties = $releaseList[0].psobject.Properties.Name
if (Compare-Object $d4gData.Data $releaseList -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/msother")
    $outputFile   = Join-Path $outputFolder "mschassistypes.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
