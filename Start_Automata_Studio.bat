@echo off
setlocal EnableExtensions
title Automata Studio - Streamlit Launcher
cd /d "%~dp0"

:: Detect whether NFA.py is in current folder or streamlit_source subfolder
set "APP_DIR=%~dp0"
if exist "%~dp0NFA.py" (
    set "APP_DIR=%~dp0"
) else if exist "%~dp0streamlit_source\NFA.py" (
    set "APP_DIR=%~dp0streamlit_source"
) else (
    echo [ERROR] Could not locate NFA.py in "%~dp0" or "%~dp0streamlit_source".
    pause
    exit /b 1
)

cd /d "%APP_DIR%"

:: Add common Windows Graphviz binary paths if installed
if exist "%ProgramFiles%\Graphviz\bin" set "PATH=%ProgramFiles%\Graphviz\bin;%PATH%"
if exist "%ProgramFiles(x86)%\Graphviz\bin" set "PATH=%ProgramFiles(x86)%\Graphviz\bin;%PATH%"
if exist "%LOCALAPPDATA%\Programs\Graphviz\bin" set "PATH=%LOCALAPPDATA%\Programs\Graphviz\bin;%PATH%"

:: Locate Python 3.9+
set "PY_CMD="
py -3 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=py -3"
    goto :found_python
)
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python"
    goto :found_python
)
for %%P in (Python313 Python312 Python311 Python310 Python39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\%%P\python.exe" (
        set "PY_CMD=\"%LOCALAPPDATA%\Programs\Python\%%P\python.exe\""
        goto :found_python
    )
)

echo ========================================================================
echo [SETUP REQUIRED] Python 3.9+ was not found on this Windows computer.
echo 1. Please install Python 3.11+ from https://www.python.org/downloads/
echo    (Check "Add python.exe to PATH" during installation), OR
echo 2. Double-click "index.html" to run the standalone offline Web version
echo    immediately with zero installation!
echo ========================================================================
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:found_python
echo ========================================================================
echo   AUTOMATA STUDIO: INTERACTIVE LEARNING LABORATORY (STREAMLIT EDITION)
echo ========================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [1/2] Creating isolated local Python environment (.venv)...
    %PY_CMD% -m venv ".venv"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

if not exist ".venv\.deps_installed_v2" (
    echo [2/2] Installing Streamlit, Graphviz, and Pandas (first-time setup)...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "requirements.txt"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Package installation failed. Check your internet connection for first-time setup.
        pause
        exit /b 1
    )
    echo ok > ".venv\.deps_installed_v2"
)

echo Launching Automata Studio in your default web browser (http://localhost:8501)...
echo (Close this window or press Ctrl+C at any time to stop the server.)
echo.
".venv\Scripts\python.exe" -m streamlit run "NFA.py" --browser.gatherUsageStats false --server.headless false
if %ERRORLEVEL% NEQ 0 pause
