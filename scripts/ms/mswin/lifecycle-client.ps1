$sourceUrls = @(
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-10-enterprise-and-education",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-11-enterprise-and-education",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-10-home-and-pro",
    "https://learn.microsoft.com/en-us/lifecycle/products/windows-11-home-and-pro"
)
$d4gData = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/lifecycle-client.json" -UseBasicParsing |
           Select-Object -ExpandProperty Content | ConvertFrom-Json

# The lifecycle product pages render dates via <local-time> custom elements.
# The datetime attribute holds the ISO value; the visible text may vary by locale.
$rxTitle   = [regex]::New('(?msi)<h1>\s*(.*?)\s*<\/h1>')
$rxRelease = [regex]::New(
    '(?msi)<td>Version (.*?)<\/td>\s*<td[^>]*>\s*<local-time[^>]*datetime="(.*?)"[^>]*>.*?<\/local-time>\s*<\/td>\s*<td[^>]*>\s*<local-time[^>]*datetime="(.*?)"[^>]*>.*?<\/local-time>'
)

$releaseList = [System.Collections.ArrayList]::new()

foreach ($sourceUrl in $sourceUrls) {
    $pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
    if ($pageData.StatusCode -ne 200) {
        Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
    }

    $skuMatch = $rxTitle.Matches($pageData.Content) | Select-Object -First 1
    $sku      = if ($skuMatch) { $skuMatch.Groups[1].Value } else { "" }

    $rxRelease.Matches($pageData.Content).ForEach{
        $releaseList.Add([PSCustomObject]@{
            Version   = $_.Groups[1].Value
            SKU       = $sku
            StartDate = $(Get-Date $_.Groups[2].Value -Format "yyyy-MM-dd")
            EndDate   = $(Get-Date $_.Groups[3].Value -Format "yyyy-MM-dd")
        }) | Out-Null
    }
}

if (-not $releaseList.Count) {
    Throw "No lifecycle entries parsed - the page structure may have changed"
}

$releaseList = $releaseList | Sort-Object Version | Select-Object Version, SKU, StartDate, EndDate -Unique

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
    $outputFile   = Join-Path $outputFolder "lifecycle-client.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
