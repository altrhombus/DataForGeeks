$sourceUrls = @(
    "https://support.microsoft.com/en-us/topic/windows-10-update-history-24ea91f4-36e7-d8fd-0ddb-d79d9d0cdbda",
    "https://aka.ms/Windows11UpdateHistory",
    "https://support.microsoft.com/en-us/topic/windows-server-2022-update-history-e1caa597-00c5-4ab9-9f3e-8212fe80b2ee"
)
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
            "https://support.microsoft.com/en-us/topic/windows-server-2022-update-history-e1caa597-00c5-4ab9-9f3e-8212fe80b2ee"
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
