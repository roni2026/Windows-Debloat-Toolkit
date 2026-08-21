@echo off
Title Windows Toolkit - GUI Launcher
echo Requesting Administrator privileges...

net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunRonin
) else (
    echo Elevating permissions...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~dpnx0\"' -Verb RunAs"
    exit
)

:RunRonin
if not exist "%~dp0src\Ronin.ps1" (
    echo Ronin source not found. Downloading from GitHub...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Get-RoninSource.ps1"
)
if exist "%~dp0Ronin.ps1" (
    echo Launching Ronin GUI...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ronin.ps1"
) else (
    echo Building Ronin from source...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0BuildRonin.ps1" -Run
)
