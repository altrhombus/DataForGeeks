$msdata = @("https://learn.microsoft.com/en-us/windows/release-health/release-information")
$d4gData = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-client-ltsc.json" | Select-Object -ExpandProperty Content | ConvertFrom-Json

$releaseList = New-Object System.Collections.ArrayList

foreach ($sourceURL in $msdata) {
    $source = Invoke-WebRequest $sourceURL -UseBasicParsing
    $allReleases = [RegEx]::New(('<tr><td>(.*?)</td>\s*<td align="left">(.*?)</td>\s*<td nowrap="">(.*?)</td>\s*<td nowrap="">(.*?)</td>\s*<td nowrap="">(.*?)</td>\s*<td nowrap="">(.*?)</td>\s*<td nowrap="">(.*?)</td>\s*<td nowrap="">(.*?)</td>\s*</tr>')).Matches($source.RawContent)
    $allReleases.ForEach{
            $releaseList.add(
                [PSCustomObject]@{
                    Version = $_.Groups[1].Value
                    ServicingOption = $_.Groups[2].Value
                    Build = $_.Groups[8].Value.Split(".")[0]
                    StartDate = $_.Groups[3].Value
                    MainstreamEndDate = $_.Groups[4].Value
                    ExtendedEndDate = $_.Groups[5].Value.Split(" ")[0]
                }
            ) | Out-Null
        
    }
}

$releaseList = $releaseList | Sort-Object Version | Select-Object Version,ServicingOption,Build,StartDate,MainstreamEndDate,ExtendedEndDate -Unique

$outputData = [PSCustomObject]@{
    "DataForGeeks"=[PSCustomObject]@{
        "LastUpdatedUTC" = (Get-Date).ToUniversalTime()
        "SourceList" = @("https://learn.microsoft.com/en-us/windows/release-health/release-information")
    }
    "Data" = $releaseList
}

$allProperties = $releaseList[0].psobject.Properties.Name

If(Compare-Object $d4gData.Data $releaseList -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot -ChildPath "../../../content/ms/mswin")
    $outputFile = Join-Path $outputFolder -ChildPath "lifecycle-client-ltsc.json"

    $jsonData = $outputData | ConvertTo-Json
    [System.IO.File]::WriteAllLines($outputFile, $jsonData)   
} else {
    Write-Host "The data has not changed."
}
