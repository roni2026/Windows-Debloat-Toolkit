# Input Device Troubleshooting Toolkit Launcher
# Run with: .\launch.ps1
# Or with args: .\launch.ps1 -Check

param(
    [switch]$Check,
    [switch]$Monitor,
    [switch]$Remap,
    [switch]$MCheck,
    [switch]$MMonitor,
    [switch]$MRemap,
    [switch]$Admin
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Input Device Troubleshooting Toolkit"

$args = @()
if ($Check) { $args += "--check" }
if ($Monitor) { $args += "--monitor" }
if ($Remap) { $args += "--remap" }
if ($MCheck) { $args += "--mcheck" }
if ($MMonitor) { $args += "--mmonitor" }
if ($MRemap) { $args += "--mremap" }
if ($Admin) { $args += "--admin" }

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Input Device Troubleshooting Toolkit v2.0" -ForegroundColor Cyan
Write-Host " Keyboard, Mouse & Trackpad" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

& python "kb_toolkit.py" $args

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
