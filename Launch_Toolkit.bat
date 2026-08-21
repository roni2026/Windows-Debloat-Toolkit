@echo off
chcp 65001 >nul
title Windows Toolkit - Unified Launcher

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
echo  Requesting Administrator privileges for GUI mode...
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunGUI
) else (
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~dpnx0\"' -Verb RunAs"
    exit
)

:RunGUI
echo  Launching Ronin GUI...
if not exist "%~dp0src\Ronin.ps1" (
    echo  Ronin source not found. Running setup to download from GitHub...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Get-RoninSource.ps1"
)
if exist "%~dp0Ronin.ps1" (
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
