$sourceUrl = "https://learn.microsoft.com/en-us/windows/release-health/release-information"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-client-ltsc.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

$rxTable = [regex]::New('(?msi)<table>(?:.*?)<tbody>(.*?)<\/tbody>')
$rxRow   = [regex]::New('(?msi)<tr>(.*?)<\/tr>')
$rxCell  = [regex]::New('(?msi)<td[^>]*>(.*?)<\/td>')
$rxHtml  = [regex]::New('(?msi)<[^>]+>')

$tables = $rxTable.Matches($pageData.Content)

# The LTSC/LTSB summary table is identified by containing "Long-Term Servicing" text.
# It has 8 columns: Version | Servicing option | Availability date | Mainstream support end date |
#   Extended support end date | Latest update for ESU | Latest revision date | Latest build
$ltscTable = $tables | Where-Object { $_.Value -match 'Long-Term Servicing' } | Select-Object -First 1

if (-not $ltscTable) {
    Throw "LTSC summary table not found - the page structure may have changed"
}

$releaseList = [System.Collections.ArrayList]::new()
$rxRow.Matches($ltscTable.Groups[1].Value).ForEach{
    $cells = $rxCell.Matches($_.Groups[1].Value)
    if ($cells.Count -ne 8) { return }

    $version          = $rxHtml.Replace($cells[0].Groups[1].Value, '').Trim()
    $servicingOption  = $rxHtml.Replace($cells[1].Groups[1].Value, '').Trim()
    $startDate        = $rxHtml.Replace($cells[2].Groups[1].Value, '').Trim()
    $mainstreamEnd    = $rxHtml.Replace($cells[3].Groups[1].Value, '').Trim()
    $extendedEnd      = ($rxHtml.Replace($cells[4].Groups[1].Value, '').Trim() -split '\s')[0]
    $latestBuild      = ($rxHtml.Replace($cells[7].Groups[1].Value, '').Trim() -split '\.')[0]

    if (-not $version -or $version -eq 'Version') { return }

    $releaseList.Add([PSCustomObject]@{
        Version           = $version
        ServicingOption   = $servicingOption
        Build             = $latestBuild
        StartDate         = $startDate
        MainstreamEndDate = $mainstreamEnd
        ExtendedEndDate   = $extendedEnd
    }) | Out-Null
}

if (-not $releaseList.Count) {
    Throw "No LTSC release entries parsed - the page structure may have changed"
}

$releaseList = $releaseList | Sort-Object Version | Select-Object Version, ServicingOption, Build, StartDate, MainstreamEndDate, ExtendedEndDate -Unique

$outputData = [PSCustomObject]@{
    DataForGeeks = [PSCustomObject]@{
        LastUpdatedUTC = (Get-Date).ToUniversalTime()
        SourceList     = @($sourceUrl)
    }
    Data = $releaseList
}

$allProperties = $releaseList[0].psobject.Properties.Name
if (Compare-Object $d4gData.Data $releaseList -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/mswin")
    $outputFile   = Join-Path $outputFolder "lifecycle-client-ltsc.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
