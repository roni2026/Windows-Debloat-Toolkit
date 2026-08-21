@echo off
chcp 65001 >nul
title Windows Toolkit - GUI

net session >nul 2>&1
if %errorLevel% == 0 (
    goto :Run
) else (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~dpnx0\"' -Verb RunAs"
    exit
)

:Run
if exist "%~dp0Ronin.ps1" (
    echo Launching Ronin GUI...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ronin.ps1"
) else (
    echo Building Ronin from source files...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0BuildRonin.ps1" -Run
)
