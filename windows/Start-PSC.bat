@echo off
setlocal
title PSC Stock Control

REM ==============================================================
REM  Double-click this file to start the app.
REM  It launches the Python backend (which also serves the React
REM  frontend on the same port) and opens the browser.
REM ==============================================================

cd /d "%~dp0\.."
set "APP_ROOT=%CD%"

REM Port the app listens on. Change here if 8000 is taken.
set "PSC_PORT=8000"

echo.
echo  Starting PSC Stock Control on http://localhost:%PSC_PORT% ...

REM --- Sanity: venv present? ---
if not exist "backend\.venv\Scripts\python.exe" (
    echo  ERROR: backend virtual environment missing.
    echo  Run  windows\Setup-Once.bat  first.
    pause
    exit /b 1
)

REM --- Sanity: frontend built? ---
if not exist "frontend\build\index.html" (
    echo  ERROR: frontend build missing.
    echo  Run  windows\Setup-Once.bat  first.
    pause
    exit /b 1
)

REM --- Kill any old instance quietly ---
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PSC_PORT% " ^| findstr LISTENING') do (
    taskkill /PID %%p /F >nul 2>&1
)

REM --- Start uvicorn in a hidden background window ---
start "PSC-Backend" /min "backend\.venv\Scripts\python.exe" -m uvicorn server:app ^
    --app-dir "%APP_ROOT%\backend" ^
    --host 0.0.0.0 --port %PSC_PORT%

REM --- Wait for it to be reachable ---
set /a tries=0
:waitloop
set /a tries+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:%PSC_PORT%/api/dashboard' -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto ready
if %tries% GEQ 20 (
    echo  App did not respond in 20 seconds. Check the PSC-Backend window.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto waitloop

:ready
start "" "http://localhost:%PSC_PORT%"

echo.
echo  ============================================
echo    PSC Stock Control is running.
echo    This PC:       http://localhost:%PSC_PORT%
echo    On network:    http://YOUR-PC-IP:%PSC_PORT%
echo    (find YOUR-PC-IP by running: ipconfig)
echo.
echo    To stop, run:  Stop-PSC.bat
echo  ============================================
echo.
timeout /t 5 /nobreak >nul
endlocal
exit /b 0
