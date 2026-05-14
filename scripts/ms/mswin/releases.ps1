$sourceUrls = @(
    "https://learn.microsoft.com/en-us/windows/release-health/release-information",
    "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"
)
$d4gData = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/releases.json" -UseBasicParsing |
           Select-Object -ExpandProperty Content | ConvertFrom-Json

$rxVersion = [regex]::New('(?msi)<strong>Version (.*?) \(OS [Bb]uild (\d{1,})\)<\/strong>')

$releaseList = [System.Collections.ArrayList]::new()

foreach ($sourceUrl in $sourceUrls) {
    $pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
    if ($pageData.StatusCode -ne 200) {
        Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
    }

    $rxVersion.Matches($pageData.Content).ForEach{
        $releaseList.Add([PSCustomObject]@{
            Version     = $_.Groups[2].Value
            FullVersion = "10.0.$($_.Groups[2].Value)"
            Build       = $_.Groups[1].Value
        }) | Out-Null
    }
}

if (-not $releaseList.Count) {
    Throw "No release entries parsed - the page structure may have changed"
}

$releaseList = $releaseList | Sort-Object Version | Select-Object Version, FullVersion, Build -Unique

$outputData = [PSCustomObject]@{
    DataForGeeks = [PSCustomObject]@{
        LastUpdatedUTC = (Get-Date).ToUniversalTime()
        SourceList     = $sourceUrls
    }
    Data = $releaseList
}

$allProperties = $releaseList[0].psobject.Properties.Name
if (Compare-Object $d4gData.Data $releaseList -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/mswin")
    $outputFile   = Join-Path $outputFolder "releases.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
