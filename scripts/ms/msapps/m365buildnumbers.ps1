$sourceUrl = "https://learn.microsoft.com/en-us/officeupdates/update-history-microsoft365-apps-by-date"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msapps/buildnumbers.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

$rxTable       = [regex]::New('(?msi)<table>(?:.*?)<tbody>(.*?)<\/tbody>')
$rxRow         = [regex]::New('(?msi)<tr>(.*?)<\/tr>')
$rxCell        = [regex]::New('(?msi)<td(?:[^>]*)>(.*?)<\/td>')
$rxLink        = [regex]::New('(?msi)<a(?:[^>])*>(.*?)<\/a>')
$rxVersionBuild = [regex]::New('(?msi)Version (.*?) \(Build {1,}(.*?)\)')

$tables = $rxTable.Matches($pageData.Content)
if ($tables.Count -lt 2) {
    Throw "Expected at least 2 tables; found $($tables.Count) - the page structure may have changed"
}

# Table at index 1 is the version history table with columns:
#   Year | Date | Current | Monthly Enterprise | Semi-Annual Enterprise Preview | Semi-Annual Enterprise
$versionHistoryRows = $rxRow.Matches($tables[1].Groups[1].Value)

$m365Releases = [System.Collections.ArrayList]::new()

$versionHistoryRows.ForEach{
    $cellData = $rxCell.Matches($_.Groups[1].Value)
    if ($cellData.Count -lt 6) { return }

    $releaseYear = $cellData[0].Groups[1].Value.Trim()
    $releaseDate = ($cellData[1].Groups[1].Value -replace '<br(?:[^>])*>', '').Trim()

    if (-not $releaseYear) {
        $releaseYear = $lastReleaseYear
    } else {
        $lastReleaseYear = $releaseYear
    }

    $release = $(Get-Date "$releaseDate $releaseYear" -Format "yyyy-MM-dd")

    $channelMap = @{
        2 = "Current"
        3 = "Monthly Enterprise"
        4 = "Semi-Annual Enterprise Preview"
        5 = "Semi-Annual Enterprise"
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
