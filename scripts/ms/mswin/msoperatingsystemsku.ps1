$msdata = @("https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getproductinfo")
$d4gData = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/msoperatingsystemsku.json" | Select-Object -ExpandProperty Content | ConvertFrom-Json

$releaseList = New-Object System.Collections.ArrayList

foreach ($sourceURL in $msdata) {
    $source = Invoke-WebRequest $sourceURL -UseBasicParsing
    $allReleases = [RegEx]::New(('<dt><b>(.*?)</b></dt>\s*<dt>(.*?)</dt>\s*</dl>\s*</td>\s*<td width="60%">\s*(.*?)\s*</td>')).Matches($source.RawContent)
    $allReleases.ForEach{
        $releaseList.add(
            [PSCustomObject]@{
                Value = $_.Groups[1].Value
                Hex = $_.Groups[2].Value
                Dec = [uint32]$_.Groups[2].Value
                Meaning = $_.Groups[3].Value
            }
        ) | Out-Null
    }
}

$releaseList = $releaseList | Sort-Object Hex | Select-Object Value,Hex,Dec,Meaning -Unique

$outputData = [PSCustomObject]@{
    "DataForGeeks"=[PSCustomObject]@{
        "LastUpdatedUTC" = (Get-Date).ToUniversalTime()
        "SourceList" = @("https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getproductinfo")
    }
    "Data" = $releaseList
}

$allProperties = $releaseList[0].psobject.Properties.Name

If(Compare-Object $d4gData.Data $releaseList -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot -ChildPath "../../../content/ms/mswin")
    $outputFile = Join-Path $outputFolder -ChildPath "msoperatingsystemsku.json"

    $jsonData = $outputData | ConvertTo-Json
    [System.IO.File]::WriteAllLines($outputFile, $jsonData)   
} else {
    Write-Host "The data has not changed."
}
