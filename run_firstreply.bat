@echo off
title FirstReply PC — Desktop AI Copilot
echo ========================================================
echo   Starting Project FirstReply PC (Desktop AI Copilot)
echo   Local-First, Quota-Aware, $0.00 Cost Guarantee
echo ========================================================
echo.

cd /d "%~dp0"

if exist "first-reply\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=first-reply\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=py"
)

echo Using Python runtime: %PYTHON_EXE%
echo Starting desktop server and tray daemon on port 8123...
echo.

%PYTHON_EXE% firstreply_pc/desktop_tray.py

pause
