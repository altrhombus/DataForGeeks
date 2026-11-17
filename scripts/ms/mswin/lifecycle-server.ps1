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
# Pages carry two table shapes, so parse row by row rather than across rows:
#   Listing table:          Listing | Start Date | Mainstream End Date | Extended End Date
#   Releases/ESU table:     Version | Start Date | End Date
$rxTitle    = [regex]::New('(?msi)<h1>\s*(.*?)\s*<\/h1>')
$rxTable    = [regex]::New('(?msi)<table[^>]*>.*?<\/table>')
$rxBodyRow  = [regex]::New('(?msi)<tr[^>]*>\s*(<td.*?)<\/tr>')
$rxCell     = [regex]::New('(?msi)<td[^>]*>(.*?)<\/td>')
$rxDateTime = [regex]::New('(?msi)<local-time[^>]*datetime="(.*?)"')

function Format-LifecycleDate([string]$cell) {
    $m = $rxDateTime.Match($cell)
    if ($m.Success) { Get-Date $m.Groups[1].Value -Format "yyyy-MM-dd" } else { $null }
}

# Microsoft labels ESU rows inconsistently across products ("ESU Year 1" vs
# "Extended Security Update Year 1"); normalize to the long form.
function Format-LifecycleTier([string]$cell) {
    $tier = ([regex]::Replace($cell, '<.*?>', '') -replace '\s+', ' ').Trim()
    $tier -replace '^ESU\b', 'Extended Security Update'
}

$releaseList = [System.Collections.ArrayList]::new()

foreach ($sourceUrl in $sourceUrls) {
    $pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
    if ($pageData.StatusCode -ne 200) {
        Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
    }

    $titleMatch = $rxTitle.Match($pageData.Content)
    $version    = if ($titleMatch.Success) { $titleMatch.Groups[1].Value.Trim() } else { '' }

    foreach ($table in $rxTable.Matches($pageData.Content)) {
        foreach ($row in $rxBodyRow.Matches($table.Value)) {
            $cells = @($rxCell.Matches($row.Groups[1].Value) | ForEach-Object { $_.Groups[1].Value })

            switch ($cells.Count) {
                4 {
                    # Listing row: start, mainstream end, extended end
                    $start = Format-LifecycleDate $cells[1]
                    $mainstreamEnd = Format-LifecycleDate $cells[2]
                    $extendedEnd = Format-LifecycleDate $cells[3]
                }
                3 {
                    # Release/ESU row: start, end. The end date is when all
                    # support for the tier stops, so it fills both end fields
                    # (matches src/scrapers/ms/win_lifecycle_server.py).
                    $start = Format-LifecycleDate $cells[1]
                    $extendedEnd = Format-LifecycleDate $cells[2]
                    $mainstreamEnd = $extendedEnd
                }
                default {
                    Throw "Unexpected $($cells.Count)-column lifecycle row on $sourceUrl - the page structure may have changed"
                }
            }

            if (-not $start) {
                Throw "Lifecycle row without a start date on $sourceUrl - the page structure may have changed"
            }

            $releaseList.Add([PSCustomObject]@{
                Version           = $version
                Tier              = Format-LifecycleTier $cells[0]
                StartDate         = $start
                MainstreamEndDate = $mainstreamEnd
                ExtendedEndDate   = $extendedEnd
            }) | Out-Null
        }
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
