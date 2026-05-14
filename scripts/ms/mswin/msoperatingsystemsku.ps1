$sourceUrl = "https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getproductinfo"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/msoperatingsystemsku.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

# Each product type row uses a definition-list structure:
#   <dt><b>PRODUCT_NAME</b></dt>  <dt>0xHEXVALUE</dt>  </dl></td>  <td ...>Description</td>
$rxEntry = [regex]::New(
    '(?msi)<dt><b>(.*?)<\/b><\/dt>\s*<dt>(.*?)<\/dt>\s*<\/dl>\s*<\/td>\s*<td[^>]*>\s*(.*?)\s*<\/td>'
)
$rxHtml = [regex]::New('(?msi)<[^>]+>')

$releaseList = [System.Collections.ArrayList]::new()
$rxEntry.Matches($pageData.Content).ForEach{
    $value   = $_.Groups[1].Value.Trim()
    $hex     = $_.Groups[2].Value.Trim()
    $meaning = $rxHtml.Replace($_.Groups[3].Value, '').Trim()

    if (-not $value.StartsWith('PRODUCT_')) { return }

    $releaseList.Add([PSCustomObject]@{
        Value   = $value
        Hex     = $hex
        Dec     = [uint32]$hex
        Meaning = $meaning
    }) | Out-Null
}

if (-not $releaseList.Count) {
    Throw "No OS SKU entries parsed - the page structure may have changed"
}

$releaseList = $releaseList | Sort-Object Hex | Select-Object Value, Hex, Dec, Meaning -Unique

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
    $outputFile   = Join-Path $outputFolder "msoperatingsystemsku.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
