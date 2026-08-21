@echo off
Title Windows Toolkit - GUI Launcher
echo Requesting Administrator privileges...

net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunVampKit
) else (
    echo Elevating permissions...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~dpnx0\"' -Verb RunAs"
    exit
)

:RunVampKit
echo Launching VampKit GUI...
if exist "%~dp0VampKit.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0VampKit.ps1"
) else (
    echo VampKit.ps1 not found. Building from source first...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0BuildVampKit.ps1" -Run
)
