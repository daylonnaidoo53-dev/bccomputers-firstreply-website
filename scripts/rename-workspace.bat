@echo off
echo ========================================================
echo  BCComputers Workspace Rename Tool
echo ========================================================
echo.
echo Windows requires Antigravity IDE to be closed so the folder
echo is no longer locked by active processes.
echo.
echo 1. Close Antigravity IDE.
echo 2. Press any key in this window to rename the folder.
echo.
pause

cd /d "%~dp0\..\.."
ren "Acend-AI-Workspace-Starter" "BCComputers-AI-Workspace"

echo.
if exist "BCComputers-AI-Workspace" (
    echo [SUCCESS] Renamed folder to: BCComputers-AI-Workspace
    echo.
    echo Next step: Open Antigravity IDE, click "File -> Open Folder",
    echo and select "BCComputers-AI-Workspace".
) else (
    echo [NOTICE] If the rename did not complete, make sure Antigravity IDE
    echo and any file explorer windows accessing files inside it are closed,
    echo or rename it directly in File Explorer.
)
echo.
pause
