$sourceUrl = "https://learn.microsoft.com/en-us/graph/api/resources/bitlockerrecoverykey?view=graph-rest-1.0"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/msgraph-bitlockerRecoveryKey.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

# The volumeType enum is described inline in the Properties table as:
# <code>1</code> (for <code>operatingSystemVolume</code>), ...
$rxEntry = [regex]::New('<code>(\d+)<\/code>\s*\(for\s*<code>([^<]+)<\/code>\)')

$volumeTypes = [System.Collections.ArrayList]::new()
$rxEntry.Matches($pageData.Content).ForEach{
    $volumeTypes.Add([PSCustomObject]@{
        VolumeTypeEnum = [int]$_.Groups[1].Value
        Description    = $_.Groups[2].Value
    }) | Out-Null
}

if (-not $volumeTypes.Count) {
    Throw "No volumeType enum entries parsed - the page structure may have changed"
}

$volumeTypes = $volumeTypes | Sort-Object VolumeTypeEnum | Select-Object VolumeTypeEnum, Description -Unique

$outputData = [PSCustomObject]@{
    DataForGeeks = [PSCustomObject]@{
        LastUpdatedUTC = (Get-Date).ToUniversalTime()
        SourceList     = @($sourceUrl)
    }
    Data = $volumeTypes
}

$allProperties = $volumeTypes[0].psobject.Properties.Name
if (Compare-Object $d4gData.Data $volumeTypes -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/msother")
    $outputFile   = Join-Path $outputFolder "msgraph-bitlockerRecoveryKey.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
