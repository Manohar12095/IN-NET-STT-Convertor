@echo off
title IN NET STT Convertor — Build EXE
color 0A
cls

echo.
echo  ============================================================
echo   IN NET STT Convertor — EXE Builder
echo   Powered by IN NET CREATIONS
echo  ============================================================
echo.

cd /d "%~dp0"

:: ── Step 1: Check Python ──────────────────────────────────
echo [1/5] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)
echo        OK

:: ── Step 2: Install build deps ───────────────────────────
echo [2/5] Installing build tools (pyinstaller, Pillow)...
pip install pyinstaller Pillow --quiet --no-warn-script-location
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install build tools.
    pause & exit /b 1
)
echo        OK

:: ── Step 3: Convert logo.png to logo.ico ─────────────────
echo [3/5] Converting logo to .ico...
python convert_icon.py
if %errorlevel% neq 0 (
    echo [WARN] Icon conversion failed. Building without custom icon.
    rem Patch spec to remove icon line so build still works
)
echo        OK

:: ── Step 4: Clean old build artefacts ────────────────────
echo [4/5] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist\InNetSTT.exe del /f /q dist\InNetSTT.exe
echo        OK

:: ── Step 5: Build ─────────────────────────────────────────
echo [5/5] Building InNetSTT.exe (this may take 1-3 minutes)...
echo.
pyinstaller InNetSTT.spec --noconfirm
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed. See output above for details.
    pause & exit /b 1
)

echo.
echo  ============================================================
echo   SUCCESS!
echo   Output: dist\InNetSTT.exe
echo   Double-click it to launch the app.
echo  ============================================================
echo.

:: Open the dist folder in Explorer
explorer dist

pause
