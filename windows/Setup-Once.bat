@echo off
title PSC Stock Control - First-time setup
echo.
echo  [ Setup-Once starting... ]
echo.

REM ==============================================================
REM  Run this ONCE after you install Python, Node.js and MongoDB.
REM  It installs backend Python packages, installs frontend
REM  packages, and builds the frontend into /frontend/build so the
REM  app is served by a single Python process later.
REM ==============================================================

cd /d "%~dp0\.."
set "APP_ROOT=%CD%"

echo  Project folder: %APP_ROOT%
echo.
echo  If you can read this line, the script is running fine.
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
    echo  WARNING: mongod not found in PATH.
    echo  Make sure MongoDB Community Server is installed.
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

echo  Installing backend Python packages ^(this takes ~2 minutes the first time^)...
call "backend\.venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r "backend\requirements.txt"
if errorlevel 1 (
    echo  ERROR: Python package install failed. See message above.
    goto :end
)

REM --- 5. Make sure backend .env exists ---
echo.
echo  [5/6] Ensuring backend .env exists...
if not exist "backend\.env" (
    echo  Creating backend\.env with defaults
    > "backend\.env" echo MONGO_URL=mongodb://localhost:27017
    >>"backend\.env" echo DB_NAME=psc_stock
    >>"backend\.env" echo CORS_ORIGINS=*
    >>"backend\.env" echo SEED_DEMO_DATA=false
)
> "frontend\.env" echo REACT_APP_BACKEND_URL=

REM --- 6. Frontend install + build ---
echo.
echo  [6/6] Installing frontend packages ^(this takes ~3-5 minutes the first time^)...
pushd frontend
call npm install --legacy-peer-deps
if errorlevel 1 (
    echo  ERROR: npm install failed.
    popd
    goto :end
)

echo  Building frontend for production...
call npm run build
if errorlevel 1 (
    echo  ERROR: npm run build failed.
    popd
    goto :end
)
popd

echo.
echo  ============================================
echo    Setup complete.
echo    You can now double-click  Start-PSC.bat
echo  ============================================

:end
echo.
echo  ---- Script finished. Press any key to close this window. ----
pause >nul
