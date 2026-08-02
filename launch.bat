@echo off
chcp 65001 >nul
title Input Device Troubleshooting Toolkit
cd /d "%~dp0"
echo ==========================================
echo  Input Device Troubleshooting Toolkit v2.0
echo  Keyboard, Mouse & Trackpad
echo ==========================================
echo.
python "kb_toolkit.py" %*
echo.
pause
