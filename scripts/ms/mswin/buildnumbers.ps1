$sourceUrls = @(
    "https://support.microsoft.com/en-us/topic/windows-10-update-history-24ea91f4-36e7-d8fd-0ddb-d79d9d0cdbda",
    "https://aka.ms/Windows11UpdateHistory",
    "https://support.microsoft.com/en-us/topic/windows-server-2022-update-history-e1caa597-00c5-4ab9-9f3e-8212fe80b2ee"
)
$hotpatchUrl = "https://support.microsoft.com/en-us/topic/release-notes-for-hotpatch-on-windows-11-enterprise-version-25h2-0bbaa1c7-5070-41ca-a7c9-4ead79602dbf"
$d4gData = Invoke-WebRequest "https://raw.githubusercontent.com/altrhombus/DataForGeeks/main/content/ms/mswin/buildnumbers.json" -UseBasicParsing |
           Select-Object -ExpandProperty Content | ConvertFrom-Json

Add-Type -AssemblyName System.Web

$rxBuildData  = [regex]::New('(?i)>(.*?) \(OS Build.*?(\d.*?)\)(.*?)<')
$rxPatchDesc  = [regex]::New('(?i)^(.*? \d{1,2}[,|] \d{4}).*?(K.*)$')

$patchList = [System.Collections.ArrayList]::new()

foreach ($sourceUrl in $sourceUrls) {
    $pageData = Invoke-WebRequest $sourceUrl -UseBasicParsing
    if ($pageData.StatusCode -ne 200) {
        Throw "Error $($pageData.StatusCode) retrieving $sourceUrl"
    }

    $rxBuildData.Matches($pageData.Content).ForEach{
        $versionList = $_.Groups[2].Value -replace 'and', ',' -replace ' ', ''
        $versionList = $versionList -split ',' | Where-Object { $_ -ne '' }

        $kbTitle    = [System.Web.HttpUtility]::HtmlDecode($_.Groups[0].Value.Substring(1, $_.Groups[0].Value.Length - 2))
        $description = [System.Web.HttpUtility]::HtmlDecode($_.Groups[1].Value)

        $patchInfo     = $rxPatchDesc.Matches($description)
        $articleNumber = $patchInfo.Groups[2].Value

        if ($articleNumber -like 'KB *') {
            $articleNumber = "KB$($articleNumber.Substring(3))"
        }
        if ($articleNumber -like '* *') {
            $articleNumber = ($articleNumber -split ' ')[0]
        }

        foreach ($version in $versionList) {
            $patchList.Add([PSCustomObject]@{
                Win10Version = "10.0.$version"
                Version      = $version
                ReleaseDate  = $(Get-Date $patchInfo.Groups[1].Value -Format "yyyy-MM-dd")
                Article      = $articleNumber
                KBTitle      = $kbTitle
                LTSCOnly     = $false
                Comment      = $_.Groups[3].Value.ToString().Trim()
            }) | Out-Null
        }
    }
}

if (-not $patchList.Count) {
    Throw "No patch entries parsed - the page structure may have changed"
}

# Hotpatch release notes — appends Hotpatch-only entries; baselines are already covered by the standard sources above
$hotpatchPage = Invoke-WebRequest $hotpatchUrl -UseBasicParsing
if ($hotpatchPage.StatusCode -ne 200) {
    Throw "Error $($hotpatchPage.StatusCode) retrieving $hotpatchUrl"
}

$rxTableRow     = [regex]::New('<tr[^>]*>(.*?)</tr>',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor
    [System.Text.RegularExpressions.RegexOptions]::Singleline)
$rxCell         = [regex]::New('<t[dh][^>]*>(.*?)</t[dh]>',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor
    [System.Text.RegularExpressions.RegexOptions]::Singleline)
$rxHtmlStrip    = [regex]::New('<[^>]+>')
$rxKB           = [regex]::New('(KB\d+)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
$rxHotpatchHref = [regex]::New('(\w+)-(\d{1,2})-(\d{4})-hotpatch.*?os-builds-(\d+)-(\d+)-and-(\d+)-(\d+)',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

$hotpatchCount = 0
foreach ($rowMatch in $rxTableRow.Matches($hotpatchPage.Content)) {
    $cells = $rxCell.Matches($rowMatch.Groups[1].Value)
    if ($cells.Count -lt 4) { continue }

    $patchType = [System.Web.HttpUtility]::HtmlDecode($rxHtmlStrip.Replace($cells[2].Groups[1].Value, '')).Trim()
    if ($patchType -like '*Baseline*') { continue }

    $kbMatch   = $rxKB.Match($cells[3].Groups[1].Value)
    $hrefMatch = $rxHotpatchHref.Match($cells[3].Groups[1].Value)
    if (-not $kbMatch.Success -or -not $hrefMatch.Success) { continue }

    $monthRaw    = $hrefMatch.Groups[1].Value
    $monthName   = $monthRaw.Substring(0, 1).ToUpper() + $monthRaw.Substring(1).ToLower()
    $releaseDate = Get-Date "$monthName $($hrefMatch.Groups[2].Value), $($hrefMatch.Groups[3].Value)" -Format "yyyy-MM-dd"
    $article     = $kbMatch.Groups[1].Value.ToUpper()

    foreach ($build in @("$($hrefMatch.Groups[4].Value).$($hrefMatch.Groups[5].Value)", "$($hrefMatch.Groups[6].Value).$($hrefMatch.Groups[7].Value)")) {
        $patchList.Add([PSCustomObject]@{
            Win10Version = "10.0.$build"
            Version      = $build
            ReleaseDate  = $releaseDate
            Article      = $article
            KBTitle      = "$monthName $($hrefMatch.Groups[2].Value), $($hrefMatch.Groups[3].Value) — $article (OS Build $build)"
            LTSCOnly     = $false
            Comment      = "Hotpatch"
        }) | Out-Null
        $hotpatchCount++
    }
}

if (-not $hotpatchCount) {
    Throw "No hotpatch entries parsed - the page structure may have changed"
}

$patchList = $patchList | Sort-Object ReleaseDate, Version | Select-Object Win10Version, Version, ReleaseDate, Article, KBTitle, LTSCOnly, Comment -Unique

# Manual overrides
$patchList = $patchList | Where-Object { $_.Win10Version -notin @('10.0.14393.5127') }  # Windows Server only
$patchList | Where-Object { $_.Win10Version -like '10.0.17763.*' -and (Get-Date $_.ReleaseDate) -ge (Get-Date '2021-05-12') } |
    ForEach-Object { $_ | Add-Member -MemberType NoteProperty -Name LTSCOnly -Value $true -Force }

$outputData = [PSCustomObject]@{
    DataForGeeks = [PSCustomObject]@{
        LastUpdatedUTC = (Get-Date).ToUniversalTime()
        SourceList     = @(
            "https://aka.ms/WindowsUpdateHistory",
            "https://aka.ms/Windows11UpdateHistory",
            "https://support.microsoft.com/en-us/topic/windows-server-2022-update-history-e1caa597-00c5-4ab9-9f3e-8212fe80b2ee",
            $hotpatchUrl
        )
    }
    Data = $patchList
}

$allProperties = $patchList[0].psobject.Properties.Name
if (Compare-Object $d4gData.Data $outputData.Data -Property $allProperties -SyncWindow 0) {
    $outputFolder = Resolve-Path (Join-Path $PSScriptRoot "../../../content/ms/mswin")
    $outputFile   = Join-Path $outputFolder "buildnumbers.json"
    [System.IO.File]::WriteAllText($outputFile, ($outputData | ConvertTo-Json -Depth 10))
} else {
    Write-Host "No changes detected."
}
