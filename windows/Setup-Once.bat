@echo off
title PSC Stock Control - First-time setup
echo.
echo  [ Setup-Once starting... ]
echo.

REM ==============================================================
REM  Run this ONCE after you install Python, Node.js and MongoDB.
REM ==============================================================

cd /d "%~dp0\.."
set "APP_ROOT=%CD%"

echo  Project folder: %APP_ROOT%
echo.
echo  Press any key to begin the checks...
pause >nul

REM --- 1. Check Python ---
echo.
echo  [1/6] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed or not in PATH.
    echo  Install Python 3.11+ from https://www.python.org/downloads/windows/
    echo  During install, tick "Add python.exe to PATH".
    goto :end
)
python --version

REM --- 2. Check Node ---
echo.
echo  [2/6] Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Node.js is not installed or not in PATH.
    echo  Install Node.js LTS from https://nodejs.org/en/download
    goto :end
)
node --version

REM --- 3. Check Mongo ---
echo.
echo  [3/6] Checking MongoDB...
where mongod >nul 2>&1
if errorlevel 1 (
    echo  WARNING: mongod not found in PATH (fine if it is running as a Windows Service).
) else (
    echo  mongod found.
)

REM --- 4. Create backend virtual environment ---
echo.
echo  [4/6] Preparing Python virtual environment...
if not exist "backend\.venv" (
    echo  Creating Python virtual environment...
    python -m venv backend\.venv
    if errorlevel 1 (
        echo  ERROR: Failed to create venv.
        goto :end
    )
)

echo  Installing backend Python packages ^(~2 minutes first time^)...
call "backend\.venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r "backend\requirements.txt"
if errorlevel 1 (
    echo  ERROR: Python package install failed. See message above.
    goto :end
)

REM --- 5. Ensure .env files ---
echo.
echo  [5/6] Ensuring .env files exist...
if not exist "backend\.env" (
    > "backend\.env" echo MONGO_URL=mongodb://localhost:27017
    >>"backend\.env" echo DB_NAME=psc_stock
    >>"backend\.env" echo CORS_ORIGINS=*
    >>"backend\.env" echo SEED_DEMO_DATA=false
)
> "frontend\.env" echo REACT_APP_BACKEND_URL=

REM --- 6. Frontend install + build via YARN (project requires it) ---
echo.
echo  [6/6] Installing frontend packages with YARN ^(~3-5 minutes first time^)...
pushd frontend

REM Prefer yarn if available, otherwise fall back to npx yarn (bundled with Node)
where yarn >nul 2>&1
if errorlevel 1 (
    echo  Using: npx --yes yarn
    set "YARN=npx --yes yarn@1.22.22"
) else (
    echo  Using: yarn (found on PATH)
    set "YARN=yarn"
)

echo.
echo  ---- yarn install ----
call %YARN% install --network-timeout 600000
if errorlevel 1 (
    echo.
    echo  ERROR: yarn install failed. Scroll up and read the red text.
    popd
    goto :end
)

echo.
echo  ---- yarn build ----
call %YARN% build
if errorlevel 1 (
    echo.
    echo  ERROR: yarn build failed. Scroll up and read the red text.
    popd
    goto :end
)
popd

if not exist "frontend\build\index.html" (
    echo.
    echo  ERROR: build finished but frontend\build\index.html is missing.
    goto :end
)

echo.
echo  ============================================
echo    Setup complete.
echo    frontend\build\index.html was created.
echo    You can now double-click  Start-PSC.bat
echo  ============================================

:end
echo.
echo  ---- Script finished. Press any key to close this window. ----
pause >nul
