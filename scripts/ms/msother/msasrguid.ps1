$sourceUrl = "https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference"
$d4gData   = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/msother/msasrguid.json" -UseBasicParsing |
             Select-Object -ExpandProperty Content | ConvertFrom-Json

$pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
if ($pageData.StatusCode -ne 200) {
    Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
}

# Each rule is an <h4> heading followed by a list containing "<strong>GUID</strong>: <code>...</code>".
$rxSection = [regex]::New('(?msi)<h4[^>]*>(.*?)<\/h4>(.*?)(?=<h[1-4][\s>]|\z)')
$rxGuid    = [regex]::New('(?msi)<strong>GUID<\/strong>\s*:\s*<code>\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s*<\/code>')
$rxHtml    = [regex]::New('(?msi)<[^>]+>')
$rxSuffix  = [regex]::New('\s*\((?:Device|User)\)\s*$')

$guids = [System.Collections.ArrayList]::new()
$rxSection.Matches($pageData.Content).ForEach{
    $guidMatch = $rxGuid.Match($_.Groups[2].Value)
    if (-not $guidMatch.Success) { return }

    $asrName = [System.Net.WebUtility]::HtmlDecode($rxHtml.Replace($_.Groups[1].Value, '')).Trim()
    $asrName = $rxSuffix.Replace($asrName, '')
    $asrGuid = $guidMatch.Groups[1].Value.ToLower()

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
if (Compare-Object $d4gData.Data $outputData.Data -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/msother")
    $outputFile   = Join-Path $outputFolder "msasrguid.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
