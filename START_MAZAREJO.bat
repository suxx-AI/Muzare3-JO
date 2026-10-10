@echo off
setlocal
chcp 65001 >nul
title Mazarejo - Live Demo
cd /d "%~dp0"
if errorlevel 1 (
    echo [ERROR] Could not enter the project folder.
    pause
    exit /b 1
)
set "DEMO_PYTHON="
if exist "%~dp0.venv\Scripts\python.exe" (
    call "%~dp0.venv\Scripts\activate.bat"
    set "DEMO_PYTHON=%~dp0.venv\Scripts\python.exe"
) else if exist "%ProgramFiles%\Python310\python.exe" (
    set "DEMO_PYTHON=%ProgramFiles%\Python310\python.exe"
) else (
    for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined DEMO_PYTHON set "DEMO_PYTHON=%%P"
)
if not defined DEMO_PYTHON (
    echo [ERROR] Python was not found. Install Python and then install requirements.txt before the demo.
    pause
    exit /b 1
)
echo [INFO] Starting Mazarejo from "%CD%"
"%DEMO_PYTHON%" "%~dp0launch_demo.py"
set "DEMO_RESULT=%ERRORLEVEL%"
if not "%DEMO_RESULT%"=="0" echo [ERROR] Startup failed. Read the reason above. The browser was not opened before readiness.
echo.
echo [INFO] This window remains open so you can review the logs.
pause
exit /b %DEMO_RESULT%
