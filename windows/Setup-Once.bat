@echo off
setlocal
title PSC Stock Control - First-time setup

REM ==============================================================
REM  Run this ONCE after you install Python, Node.js and MongoDB.
REM  It installs the backend Python packages, installs frontend
REM  packages, and builds the frontend into /frontend/build so the
REM  app is served by a single Python process later.
REM ==============================================================

cd /d "%~dp0\.."
set "APP_ROOT=%CD%"

echo.
echo  ============================================
echo    PSC Stock Control - First-time setup
echo    Project folder: %APP_ROOT%
echo  ============================================
echo.

REM --- 1. Check Python ---
where python >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed or not in PATH.
    echo  Install Python 3.11+ from https://www.python.org/downloads/windows/
    echo  During install, tick "Add python.exe to PATH".
    pause
    exit /b 1
)

REM --- 2. Check Node ---
where node >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Node.js is not installed or not in PATH.
    echo  Install Node.js LTS from https://nodejs.org/en/download
    pause
    exit /b 1
)

REM --- 3. Check Mongo ---
where mongod >nul 2>&1
if errorlevel 1 (
    echo  WARNING: mongod not found in PATH.
    echo  Make sure MongoDB Community Server is installed and running as a
    echo  Windows Service (default option in the MongoDB installer).
    echo.
)

REM --- 4. Create backend virtual environment ---
if not exist "backend\.venv" (
    echo  Creating Python virtual environment...
    python -m venv backend\.venv
)

echo  Installing backend Python packages (this takes ~2 minutes the first time)...
call backend\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo  ERROR: Python package install failed. See message above.
    pause
    exit /b 1
)

REM --- 5. Make sure backend .env exists ---
if not exist "backend\.env" (
    echo  Creating backend\.env with defaults
    > backend\.env echo MONGO_URL=mongodb://localhost:27017
    >>backend\.env echo DB_NAME=psc_stock
    >>backend\.env echo CORS_ORIGINS=*
    >>backend\.env echo SEED_DEMO_DATA=false
)

REM --- 6. Frontend .env: point to same origin (empty URL = relative /api) ---
> frontend\.env echo REACT_APP_BACKEND_URL=

REM --- 7. Frontend install + build ---
echo.
echo  Installing frontend packages (this takes ~3-5 minutes the first time)...
pushd frontend
call npm install --legacy-peer-deps
if errorlevel 1 (
    echo  ERROR: npm install failed.
    popd
    pause
    exit /b 1
)

echo  Building frontend for production...
call npm run build
if errorlevel 1 (
    echo  ERROR: npm run build failed.
    popd
    pause
    exit /b 1
)
popd

echo.
echo  ============================================
echo    Setup complete.
echo    You can now double-click  Start-PSC.bat
echo  ============================================
echo.
pause
endlocal
exit /b 0
