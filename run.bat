@echo off
title IN NET STT Convertor — Launcher
color 0B
cls

echo.
echo  ============================================================
echo   IN NET STT Convertor
echo   Powered by IN NET CREATIONS
echo   Created by Manohar  ^|  innetcreations@gmail.com
echo  ============================================================
echo.

:: ── Check Python ──────────────────────────────────────────
echo [1/3] Checking Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ from https://python.org
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
echo        Python found. OK

:: ── Install / verify dependencies ─────────────────────────
echo [2/3] Checking dependencies (flask, edge-tts)...
python -c "import flask, edge_tts" >nul 2>&1
if %errorlevel% neq 0 (
    echo        Installing dependencies...
    pip install flask edge-tts --quiet --no-warn-script-location
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Check your internet connection and try again.
        pause
        exit /b 1
    )
)
echo        Dependencies OK

:: ── Launch Flask server ────────────────────────────────────
echo [3/3] Starting IN NET STT Convertor...
echo.
echo  ============================================================
echo   Access at: http://127.0.0.1:5000
echo   Press Ctrl+C to stop the server
echo  ============================================================
echo.

:: Change to the script's own directory so Python can find app.py
cd /d "%~dp0"
python app.py

:: ── Pause on exit so user can see any error messages ──────
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The server stopped unexpectedly. See the message above.
    pause
)
