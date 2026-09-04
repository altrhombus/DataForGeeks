$sourceUrl = "https://learn.microsoft.com/en-us/officeupdates/update-history-microsoft365-apps-by-date"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msapps/buildnumbers.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

$rxTable       = [regex]::New('(?msi)<table>(?:.*?)<thead>(.*?)<\/thead>(?:.*?)<tbody>(.*?)<\/tbody>')
$rxRow         = [regex]::New('(?msi)<tr>(.*?)<\/tr>')
$rxCell        = [regex]::New('(?msi)<t[dh](?:[^>]*)>(.*?)<\/t[dh]>')
$rxLink        = [regex]::New('(?msi)<a(?:[^>])*>(.*?)<\/a>')
$rxHtmlStrip   = [regex]::New('<[^>]+>')
$rxVersionBuild = [regex]::New('(?msi)Version (.*?) \(Build {1,}(.*?)\)')

# Header text -> channel label. Column positions are derived from the header
# row at parse time so a column insertion, reorder, or removal cannot silently
# mislabel channels.
$channelHeaderMap = [ordered]@{
    "Current Channel"                = "Current"
    "Monthly Enterprise Channel"     = "Monthly Enterprise"
    "Semi-Annual Enterprise Channel" = "Semi-Annual Enterprise"
}

$historyTable = $null
foreach ($tableMatch in $rxTable.Matches($pageData.Content)) {
    $headerRow = $rxRow.Match($tableMatch.Groups[1].Value)
    if (-not $headerRow.Success) { continue }

    $headerCells = @($rxCell.Matches($headerRow.Groups[1].Value) | ForEach-Object { $rxHtmlStrip.Replace($_.Groups[1].Value, '').Trim() })
    if ($headerCells -notcontains 'Year' -or $headerCells -notcontains 'Release Date') { continue }

    $matchedChannels = @($headerCells | Where-Object { $channelHeaderMap.Contains($_) })
    if ($matchedChannels.Count -ne $channelHeaderMap.Count) {
        Throw "History table channel columns changed: expected $(@($channelHeaderMap.Keys) -join ', '); found $($matchedChannels -join ', ') - the page structure may have changed"
    }

    $historyTable = [PSCustomObject]@{ Headers = $headerCells; Body = $tableMatch.Groups[2].Value }
    break
}

if (-not $historyTable) {
    Throw "Version history table not found - the page structure may have changed"
}

$yearIndex  = [array]::IndexOf($historyTable.Headers, 'Year')
$dateIndex  = [array]::IndexOf($historyTable.Headers, 'Release Date')
$channelMap = @{}
foreach ($header in $channelHeaderMap.Keys) {
    $channelMap[[array]::IndexOf($historyTable.Headers, $header)] = $channelHeaderMap[$header]
}
$maxIndex = ($channelMap.Keys + $yearIndex + $dateIndex | Measure-Object -Maximum).Maximum

$versionHistoryRows = $rxRow.Matches($historyTable.Body)

$m365Releases = [System.Collections.ArrayList]::new()

$versionHistoryRows.ForEach{
    $cellData = $rxCell.Matches($_.Groups[1].Value)
    if ($cellData.Count -le $maxIndex) { return }

    $releaseYear = $cellData[$yearIndex].Groups[1].Value.Trim()
    $releaseDate = ($cellData[$dateIndex].Groups[1].Value -replace '<br(?:[^>])*>', '').Trim()

    if (-not $releaseYear) {
        $releaseYear = $lastReleaseYear
    } else {
        $lastReleaseYear = $releaseYear
    }

    try {
        $release = Get-Date "$releaseDate $releaseYear" -Format "yyyy-MM-dd" -ErrorAction Stop
    } catch {
        return
    }

    foreach ($colIndex in $channelMap.Keys) {
        $channelName  = $channelMap[$colIndex]
        $channelLinks = $rxLink.Matches($cellData[$colIndex].Groups[1].Value)

        $channelLinks.groups.where{ $_.Name -eq 1 }.ForEach{
            $rxVersionBuild.Matches($_.Value).ForEach{
                $m365Releases.Add([PSCustomObject]@{
                    ReleaseDate = $release
                    Channel     = $channelName
                    Build       = $_.Groups[2].Value
                    Version     = $_.Groups[1].Value
                    FullBuild   = "16.0.$($_.Groups[2].Value)"
                }) | Out-Null
            }
        }
    }
}

if (-not $m365Releases.Count) {
    Throw "No M365 release entries parsed - the page structure may have changed"
}

$m365Releases = $m365Releases | Sort-Object ReleaseDate -Descending | Select-Object ReleaseDate, Channel, Build, Version, FullBuild -Unique

$outputData = [PSCustomObject]@{
    DataForGeeks = [PSCustomObject]@{
        LastUpdatedUTC = (Get-Date).ToUniversalTime()
        SourceList     = @($sourceUrl)
    }
    Data = $m365Releases
}

$allProperties = $m365Releases[0].psobject.Properties.Name
if (Compare-Object $d4gData.Data $outputData.Data -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/msapps")
    $outputFile   = Join-Path $outputFolder "buildnumbers.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
