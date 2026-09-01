@echo off
title PSC Stock Control
echo.
echo  [ Start-PSC starting... ]
echo.

cd /d "%~dp0\.."
set "APP_ROOT=%CD%"
set "PSC_PORT=8000"

echo  Project folder: %APP_ROOT%
echo  Target port:    %PSC_PORT%
echo.

REM --- Sanity: venv present? ---
if not exist "backend\.venv\Scripts\python.exe" (
    echo  ERROR: backend virtual environment missing.
    echo  Run  windows\Setup-Once.bat  first.
    goto :end
)

REM --- Sanity: frontend built? ---
if not exist "frontend\build\index.html" (
    echo  ERROR: frontend build missing.
    echo  Run  windows\Setup-Once.bat  first.
    goto :end
)

REM --- Kill any old instance quietly ---
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PSC_PORT% " ^| findstr LISTENING') do (
    taskkill /PID %%p /F >nul 2>&1
)

echo  Starting backend on http://localhost:%PSC_PORT% ...
start "PSC-Backend" /min "%APP_ROOT%\backend\.venv\Scripts\python.exe" -m uvicorn server:app --app-dir "%APP_ROOT%\backend" --host 0.0.0.0 --port %PSC_PORT%

REM --- Wait for it to be reachable ---
set /a tries=0
:waitloop
set /a tries+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:%PSC_PORT%/api/dashboard' -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto ready
if %tries% GEQ 20 (
    echo  App did not respond in 20 seconds. Check the PSC-Backend window.
    goto :end
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

:end
echo.
echo  ---- Press any key to close this window. ----
pause >nul
