@echo off
TITLE FirstReply PC — Environment Setup
echo ===================================================
echo   FirstReply PC — Automated Environment Setup
echo ===================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from python.org and rerun.
    pause
    exit /b 1
)

echo [1/3] Creating Python virtual environment (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/3] Activating virtual environment and upgrading pip...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo [3/3] Installing FirstReply PC dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Setup Complete!
echo   Run 'run_firstreply.bat' to launch the system.
echo   Run 'pytest firstreply_pc/tests' to run tests.
echo ===================================================
pause
