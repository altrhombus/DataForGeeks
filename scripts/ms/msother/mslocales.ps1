$sourceUrl = "https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/6c085406-a698-4e12-9d4d-c3b0ee3dbc4a"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/mslocales.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

$rxTable = [regex]::New('(?msi)<table>(?:.*?)<tbody>(.*?)<\/tbody>')
$rxRow   = [regex]::New('(?msi)<tr>(.*?)<\/tr>')
$rxCell  = [regex]::New('(?msi)<td(?:[^>]*)>(.*?)<\/td>')
$rxHtml  = [regex]::New('(?msi)<[^>]+>')

$tables = $rxTable.Matches($pageData.Content)
if ($tables.Count -lt 1) {
    Throw "No tables found - the page structure may have changed"
}

$locales = [System.Collections.ArrayList]::new()
$rxRow.Matches($tables[0].Groups[1].Value).ForEach{
    $cellData = $rxCell.Matches($_.Groups[1].Value)
    if ($cellData.Count -lt 3) { return }

    $langCode = $rxHtml.Replace($cellData[0].Groups[1].Value, '').Trim()
    $langName = $rxHtml.Replace($cellData[1].Groups[1].Value, '').Trim()
    $langTag  = $rxHtml.Replace($cellData[2].Groups[1].Value, '').Trim()

    if ($langCode -eq "Any other value" -or -not $langCode) { return }

    $locales.Add([PSCustomObject]@{
        LangCode    = [int]$langCode
        LangCodeHex = '{0:X4}' -f [int]$langCode
        LangName    = $langName
        LangTag     = $langTag
    }) | Out-Null
}

if (-not $locales.Count) {
    Throw "No locale entries parsed - the page structure may have changed"
}

$locales = $locales | Sort-Object LangCode | Select-Object LangCode, LangCodeHex, LangName, LangTag -Unique

$outputData = [PSCustomObject]@{
    DataForGeeks = [PSCustomObject]@{
        LastUpdatedUTC = (Get-Date).ToUniversalTime()
        SourceList     = @($sourceUrl)
    }
    Data = $locales
}

$allProperties = $locales[0].psobject.Properties.Name
if (Compare-Object $d4gData.Data $outputData.Data -Property $allProperties) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/msother")
    $outputFile   = Join-Path $outputFolder "mslocales.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
