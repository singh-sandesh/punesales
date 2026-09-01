@echo off
setlocal
title PSC Stock Control - Starting...

REM =============================================================
REM  PSC Stock Control - one-click launcher
REM  Place this file inside your project folder (same folder as
REM  docker-compose.yml). Double-click it (or its desktop shortcut)
REM  to start the app and open it in your browser.
REM =============================================================

cd /d "%~dp0"

echo.
echo  ============================================
echo    PSC Stock Control - Starting up
echo  ============================================
echo.

REM --- 1. Make sure Docker Desktop is running ---
docker info >nul 2>&1
if errorlevel 1 (
    echo  Docker is not running yet. Launching Docker Desktop...
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"

    echo  Waiting for Docker to be ready (this can take 30-60 seconds)...
    :waitdocker
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 goto waitdocker
    echo  Docker is ready.
    echo.
)

REM --- 2. Make sure .env exists ---
if not exist ".env" (
    if exist ".env.example" (
        echo  No .env file found - creating one from .env.example
        copy ".env.example" ".env" >nul
    )
)

REM --- 3. Start the containers ---
echo  Starting containers (mongo + backend + frontend)...
docker compose up -d
if errorlevel 1 (
    echo.
    echo  ERROR: Failed to start containers. See message above.
    echo.
    pause
    exit /b 1
)

echo.
echo  Waiting for the app to be ready...
timeout /t 5 /nobreak >nul

REM --- 4. Open the app in the default browser ---
start "" "http://localhost"

echo.
echo  ============================================
echo    PSC Stock Control is running.
echo    Open on this PC:  http://localhost
echo    On your network: http://<this-PC-IP>
echo  ============================================
echo.
echo  You can close this window - the app keeps running
echo  in the background until you run Stop-PSC.bat
echo  or shut down the PC.
echo.
timeout /t 6 /nobreak >nul
endlocal
exit /b 0
