@echo off
setlocal
title Discord Music Bot
color 0A

echo ====================================
echo    Discord Music Bot - Uruchamianie
echo ====================================
echo.

cd /d "%~dp0"
set "PROJECT_DIR=%~dp0"

REM Wybierz folder venv (domyslnie .venv). Mozesz nadpisac przez BOT_VENV
set "VENV_DIR=.venv"
if defined BOT_VENV set "VENV_DIR=%BOT_VENV%"

set "PYTHON_EXE="
if exist "%VENV_DIR%\Scripts\python.exe" set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
if not defined PYTHON_EXE if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"

if not defined PYTHON_EXE (
    for /f "delims=" %%F in ('dir /b /s /a:-d /o:-d pyvenv.cfg 2^>nul') do (
        set "PYTHON_EXE=%%~dpF\Scripts\python.exe"
        goto :python_found
    )
)
:python_found

if defined PYTHON_EXE (
    echo [OK] Uzywam Pythona z venv: %PYTHON_EXE%
) else (
    echo [INFO] Brak srodowiska wirtualnego - uzywam globalnego Python
    set "PYTHON_EXE=python"
)

echo.
echo [INFO] Uruchamianie bota...
echo [INFO] Nacisnij Ctrl+C aby zatrzymac bota
echo ====================================
echo.

"%PYTHON_EXE%" "%PROJECT_DIR%main.py"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Bot zakonczyl dzialanie z bledem! (kod %EXIT_CODE%)
    echo [ERROR] Sprawdz logi powyzej
    pause
    endlocal & exit /b %EXIT_CODE%
)

echo.
echo [INFO] Bot zostal zatrzymany
pause
endlocal
