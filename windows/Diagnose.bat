@echo off
title PSC Diagnostic
echo.
echo  ============================================
echo    PSC Diagnostic - checking your PC
echo  ============================================
echo.

echo  Script folder : %~dp0
echo  Working dir   : %CD%
echo.

cd /d "%~dp0\.."
echo  App root      : %CD%
echo.

echo  --- Python ---
where python
python --version 2>&1
echo.

echo  --- Node.js ---
where node
node --version 2>&1
echo.

echo  --- npm ---
where npm
call npm --version 2>&1
echo.

echo  --- MongoDB (mongod) ---
where mongod
mongod --version 2>&1
echo.

echo  --- Project files ---
if exist "backend\server.py"          (echo  [OK]  backend\server.py)          else (echo  [MISSING] backend\server.py)
if exist "backend\requirements.txt"   (echo  [OK]  backend\requirements.txt)   else (echo  [MISSING] backend\requirements.txt)
if exist "backend\.venv"              (echo  [OK]  backend\.venv folder)       else (echo  [not yet] backend\.venv - run Setup-Once)
if exist "frontend\package.json"      (echo  [OK]  frontend\package.json)      else (echo  [MISSING] frontend\package.json)
if exist "frontend\build\index.html"  (echo  [OK]  frontend\build\index.html) else (echo  [not yet] frontend\build - run Setup-Once)
echo.

echo  ============================================
echo    Diagnostic done.
echo    Screenshot this whole window and send it.
echo  ============================================
echo.
pause
