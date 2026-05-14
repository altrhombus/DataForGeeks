$sourceUrls = @(
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2008",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2008-r2",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2012",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2012-r2",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2016",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2019",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2022",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2025"
)
$d4gData = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-server.json" -UseBasicParsing |
           Select-Object -ExpandProperty Content | ConvertFrom-Json

# The lifecycle product pages render dates via <local-time> custom elements.
# The datetime attribute holds the ISO value; the visible text may vary by locale.
$rxTitle   = [regex]::New('(?msi)<h1>\s*(.*?)\s*<\/h1>')
$rxRelease = [regex]::New(
    '(?msi)<td>(.*?)<\/td>\s*<td[^>]*>\s*<local-time[^>]*datetime="(.*?)"[^>]*>.*?<\/local-time>\s*<\/td>\s*' +
    '<td[^>]*>\s*<local-time[^>]*datetime="(.*?)"[^>]*>.*?<\/local-time>\s*<\/td>\s*' +
    '<td[^>]*>\s*<local-time[^>]*datetime="(.*?)"[^>]*>.*?<\/local-time>'
)

$releaseList = [System.Collections.ArrayList]::new()

foreach ($sourceUrl in $sourceUrls) {
    $pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
    if ($pageData.StatusCode -ne 200) {
        Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
    }

    $titleMatch = $rxTitle.Match($pageData.Content)
    $version    = if ($titleMatch.Success) { $titleMatch.Groups[1].Value.Trim() } else { '' }

    $rxRelease.Matches($pageData.Content).ForEach{
        $releaseList.Add([PSCustomObject]@{
            Version           = $version
            Tier              = $_.Groups[1].Value.Trim()
            StartDate         = $(Get-Date $_.Groups[2].Value -Format "yyyy-MM-dd")
            MainstreamEndDate = $(Get-Date $_.Groups[3].Value -Format "yyyy-MM-dd")
            ExtendedEndDate   = $(Get-Date $_.Groups[4].Value -Format "yyyy-MM-dd")
        }) | Out-Null
    }
}

if (-not $releaseList.Count) {
    Throw "No lifecycle entries parsed - the page structure may have changed"
}

$releaseList = $releaseList | Sort-Object Version, Tier | Select-Object Version, Tier, StartDate, MainstreamEndDate, ExtendedEndDate -Unique

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
    $outputFile   = Join-Path $outputFolder "lifecycle-server.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
