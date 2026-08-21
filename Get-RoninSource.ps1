<#
.SYNOPSIS
    Downloads Project Ronin source files from GitHub into this repository.

.DESCRIPTION
    Fetches src/ and ui/ from keiretrogaming/Project-Ronin (MIT licensed).
    Run this once before building or launching the GUI for the first time.
    Also runs automatically via the launchers if src/Ronin.ps1 is missing.

.NOTES
    Both repos are owned by roni2026. Project Ronin is MIT licensed.
    Source: https://github.com/keiretrogaming/Project-Ronin
#>

Param([switch]$BuildAfter, [switch]$RunAfter)

$BaseDir = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($BaseDir)) { $BaseDir = $PWD.Path }

$RepoBase = "https://raw.githubusercontent.com/keiretrogaming/Project-Ronin/main"

$Files = @{
    "src/Ronin.ps1"             = "$RepoBase/src/Ronin.ps1"
    "src/RoninCore.ps1"         = "$RepoBase/src/RoninCore.ps1"
    "src/RoninDB.ps1"           = "$RepoBase/src/RoninDB.ps1"
    "ui/Ronin.xaml"             = "$RepoBase/ui/Ronin.xaml"
}

Write-Host ""
Write-Host "  Downloading Project Ronin source files..." -ForegroundColor Cyan
Write-Host "  Source: github.com/keiretrogaming/Project-Ronin" -ForegroundColor Gray
Write-Host ""

$ok = 0
$fail = 0

foreach ($dest in $Files.Keys) {
    $url      = $Files[$dest]
    $outPath  = Join-Path $BaseDir $dest
    $outDir   = Split-Path $outPath -Parent

    if (!(Test-Path $outDir)) {
        New-Item -Path $outDir -ItemType Directory -Force | Out-Null
    }

    Write-Host "  Downloading $dest..." -NoNewline
    try {
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile($url, $outPath)
        Write-Host " OK" -ForegroundColor Green
        $ok++
    } catch {
        Write-Host " FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $fail++
    }
}

Write-Host ""
if ($fail -eq 0) {
    Write-Host "  All files downloaded successfully ($ok files)." -ForegroundColor Green
} else {
    Write-Host "  $ok downloaded, $fail failed. Check your internet connection." -ForegroundColor Yellow
}
Write-Host ""

if ($BuildAfter -and $fail -eq 0) {
    Write-Host "  Building Ronin monolith..." -ForegroundColor Cyan
    & (Join-Path $BaseDir "BuildRonin.ps1") -Run:$RunAfter
} elseif ($RunAfter -and (Test-Path (Join-Path $BaseDir "src\Ronin.ps1"))) {
    Write-Host "  Launching Ronin..." -ForegroundColor Cyan
    & (Join-Path $BaseDir "BuildRonin.ps1") -Run
}
