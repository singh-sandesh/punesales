@echo off
title PSC Stock Control - First-time setup
cd /d "%~dp0\.."
set "APP_ROOT=%CD%"
set "LOG=%APP_ROOT%\setup-log.txt"

REM Fresh log
> "%LOG%" echo === PSC Setup log - %DATE% %TIME% ===
>>"%LOG%" echo APP_ROOT=%APP_ROOT%

echo.
echo  =====================================================
echo    PSC Stock Control - First-time setup
echo    A full log is being written to:
echo    %LOG%
echo  =====================================================
echo.
echo  If anything goes wrong, send me that file.
echo.
echo  Press any key to begin...
pause >nul

REM ---------- STEP 1: Python ----------
echo.
echo  [1/6] Checking Python...
where python >>"%LOG%" 2>&1
if errorlevel 1 goto no_python
python --version
python --version >>"%LOG%" 2>&1
echo   ok.
echo.
echo  Press any key to continue to Node check...
pause >nul
goto step2

:no_python
echo  ERROR: Python is not in PATH.
echo  Install Python 3.11+ from https://www.python.org/downloads/windows/
echo  and TICK "Add python.exe to PATH".
goto end

REM ---------- STEP 2: Node ----------
:step2
echo.
echo  [2/6] Checking Node.js...
where node >>"%LOG%" 2>&1
if errorlevel 1 goto no_node
node --version
node --version >>"%LOG%" 2>&1
echo   ok.
echo.
echo  Press any key to continue to backend setup...
pause >nul
goto step3

:no_node
echo  ERROR: Node.js is not in PATH.
echo  Install Node.js LTS from https://nodejs.org/en/download
goto end

REM ---------- STEP 3: Backend venv + pip ----------
:step3
echo.
echo  [3/6] Backend virtual environment ^& pip install...
if exist "backend\.venv\Scripts\python.exe" goto pip_install
echo   Creating venv...
python -m venv "backend\.venv" >>"%LOG%" 2>&1
if errorlevel 1 goto venv_fail

:pip_install
call "backend\.venv\Scripts\activate.bat"
echo   Upgrading pip...
python -m pip install --upgrade pip >>"%LOG%" 2>&1
echo   Installing backend requirements (may take ~2 min)...
pip install -r "backend\requirements.txt" >>"%LOG%" 2>&1
if errorlevel 1 goto pip_fail
echo   ok.
echo.
echo  Press any key to continue to .env files...
pause >nul
goto step4

:venv_fail
echo  ERROR: could not create venv. See %LOG%.
goto end

:pip_fail
echo  ERROR: pip install failed. See %LOG%.
goto end

REM ---------- STEP 4: .env files ----------
:step4
echo.
echo  [4/6] Writing .env files...
if exist "backend\.env" goto env_frontend
> "backend\.env" echo MONGO_URL=mongodb://localhost:27017
>>"backend\.env" echo DB_NAME=psc_stock
>>"backend\.env" echo CORS_ORIGINS=*
>>"backend\.env" echo SEED_DEMO_DATA=false

:env_frontend
> "frontend\.env" echo REACT_APP_BACKEND_URL=
echo   ok.
echo.
echo  Press any key to continue to frontend install...
pause >nul
goto step5

REM ---------- STEP 5: yarn install ----------
:step5
echo.
echo  [5/6] Frontend install with YARN (this is the slow step, be patient)...
cd /d "%APP_ROOT%\frontend"
echo   Working dir now: %CD%
where yarn >nul 2>&1
if errorlevel 1 goto use_npx_yarn
set "YARN=yarn"
goto do_install

:use_npx_yarn
set "YARN=npx --yes yarn@1.22.22"

:do_install
echo   Running: %YARN% install  (output also saved to setup-log.txt)
echo. >>"%LOG%"
echo ==== yarn install ==== >>"%LOG%"
call %YARN% install --network-timeout 600000 >>"%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo   yarn install exit code: %RC%
echo yarn install exit code: %RC% >>"%LOG%"
if not "%RC%"=="0" goto yarn_install_fail
if not exist "node_modules\react-scripts" goto no_node_modules
echo   ok. node_modules created.
echo.
echo  Press any key to continue to frontend BUILD...
pause >nul
goto step6

:no_node_modules
echo.
echo  ERROR: yarn install said it worked but node_modules\react-scripts is missing.
echo  See %LOG% for details.
cd /d "%APP_ROOT%"
goto end

:yarn_install_fail
echo.
echo  ERROR: yarn install failed. Scroll up for the error, or see %LOG%.
cd /d "%APP_ROOT%"
goto end

REM ---------- STEP 6: yarn build ----------
:step6
echo.
echo  [6/6] Building frontend (~1-3 min, output also saved to setup-log.txt)...
echo. >>"%LOG%"
echo ==== yarn build ==== >>"%LOG%"
call %YARN% build >>"%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo   yarn build exit code: %RC%
echo yarn build exit code: %RC% >>"%LOG%"
cd /d "%APP_ROOT%"
if not "%RC%"=="0" goto build_fail
if not exist "frontend\build\index.html" goto build_missing

echo.
echo  =====================================================
echo    SUCCESS. frontend\build\index.html created.
echo    You can now double-click  Start-PSC.bat
echo  =====================================================
goto end

:build_fail
echo  ERROR: yarn build failed. Scroll up or see %LOG%.
goto end

:build_missing
echo  ERROR: build finished but frontend\build\index.html is missing.
goto end

:end
echo.
echo  ---- Script finished. Log saved to %LOG% ----
echo  ---- Press any key to close this window. ----
pause >nul
