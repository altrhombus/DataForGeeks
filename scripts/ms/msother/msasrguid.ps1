$sourceUrl = "https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/msasrguid.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

$rxTable  = [regex]::New('(?msi)<table>(?:.*?)<tbody>(.*?)<\/tbody>')
$rxRow    = [regex]::New('(?msi)<tr>(.*?)<\/tr>')
$rxCell   = [regex]::New('(?msi)<td(?:[^>]*)>(.*?)<\/td>')
$rxHtml   = [regex]::New('(?msi)<[^>]+>')
$rxUuid   = [regex]::New('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

$tables = $rxTable.Matches($pageData.Content)

# Find the GUID matrix table by looking for rows whose second cell contains a UUID.
$guidTable = $null
foreach ($table in $tables) {
    $rows = $rxRow.Matches($table.Groups[1].Value)
    if ($rows.Count -eq 0) { continue }
    $cells = $rxCell.Matches($rows[0].Groups[1].Value)
    if ($cells.Count -eq 2 -and $rxUuid.IsMatch($cells[1].Groups[1].Value)) {
        $guidTable = $table
        break
    }
}

if (-not $guidTable) {
    Throw "GUID matrix table not found - the page structure may have changed"
}

$guids = [System.Collections.ArrayList]::new()
$rxRow.Matches($guidTable.Groups[1].Value).ForEach{
    $cells = $rxCell.Matches($_.Groups[1].Value)
    if ($cells.Count -lt 2) { return }

    $asrName = $rxHtml.Replace($cells[0].Groups[1].Value, '').Trim()
    $asrGuid = $rxHtml.Replace($cells[1].Groups[1].Value, '').Trim()

    if (-not $rxUuid.IsMatch($asrGuid)) { return }

    $guids.Add([PSCustomObject]@{
        AsrName = $asrName
        AsrGuid = $asrGuid
    }) | Out-Null
}

if (-not $guids.Count) {
    Throw "No GUID entries parsed - the page structure may have changed"
}

$guids = $guids | Sort-Object AsrGuid | Select-Object AsrName, AsrGuid -Unique

$outputData = [PSCustomObject]@{
    DataForGeeks = [PSCustomObject]@{
        LastUpdatedUTC = (Get-Date).ToUniversalTime()
        SourceList     = @($sourceUrl)
    }
    Data = $guids
}

$allProperties = $guids[0].psobject.Properties.Name
if (Compare-Object $d4gData.Data $outputData.Data -Property $allProperties) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/msother")
    $outputFile   = Join-Path $outputFolder "msasrguid.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
