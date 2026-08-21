@echo off
chcp 65001 >nul
title Windows Toolkit - Unified Launcher

:START
cls
echo.
echo  ============================================================
echo    WINDOWS TOOLKIT  ^|  Unified Debloat ^& Troubleshooting
echo  ============================================================
echo.
echo   [1] GUI Mode      - Debloat, Optimization ^& Maintenance
echo                       (Project Ronin - WPF interface)
echo.
echo   [2] CLI Mode      - Full Hardware Diagnostics
echo                       (Python toolkit - keyboard, mouse,
echo                        storage, audio, network, repair...)
echo.
echo   [0] Exit
echo.
set /p CHOICE="  Select option: "

if "%CHOICE%"=="1" goto :GUI
if "%CHOICE%"=="2" goto :CLI
if "%CHOICE%"=="0" goto :EXIT
echo  Invalid option. Try again.
pause
goto :START

:GUI
echo.
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunGUI
) else (
    echo  Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~dpnx0\"' -Verb RunAs"
    exit
)

:RunGUI
if exist "%~dp0Ronin.ps1" (
    echo  Launching Ronin GUI...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ronin.ps1"
) else (
    echo  Building Ronin from source...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0BuildRonin.ps1" -Run
)
goto :EXIT

:CLI
echo.
echo  Launching Hardware Diagnostics Toolkit...
cd /d "%~dp0"
python "kb_toolkit.py" %*
echo.
pause
goto :EXIT

:EXIT
exit /b 0
