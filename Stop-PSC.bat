@echo off
setlocal
title PSC Stock Control - Stopping...

cd /d "%~dp0"

echo.
echo  ============================================
echo    PSC Stock Control - Shutting down
echo  ============================================
echo.

docker compose down
if errorlevel 1 (
    echo.
    echo  ERROR: Could not stop containers (is Docker running?).
    pause
    exit /b 1
)

echo.
echo  All PSC containers have been stopped.
echo  Your data is safe - it stays in the mongo volume.
echo.
timeout /t 4 /nobreak >nul
endlocal
exit /b 0
