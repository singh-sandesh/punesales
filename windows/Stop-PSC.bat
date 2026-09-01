@echo off
setlocal
title Stopping PSC Stock Control

set "PSC_PORT=8000"

echo.
echo  Stopping PSC Stock Control...

set "found=0"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PSC_PORT% " ^| findstr LISTENING') do (
    taskkill /PID %%p /F >nul 2>&1
    if not errorlevel 1 set "found=1"
)

if "%found%"=="1" (
    echo  App stopped.
) else (
    echo  Nothing was running on port %PSC_PORT%.
)

timeout /t 3 /nobreak >nul
endlocal
exit /b 0
