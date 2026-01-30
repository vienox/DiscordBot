@echo off
title Discord Music Bot
color 0A

echo ====================================
echo    Discord Music Bot - Uruchamianie
echo ====================================
echo.

cd /d "%~dp0"

REM Sprawdź czy istnieje venv
if exist ".venv\Scripts\activate.bat" (
    echo [OK] Aktywowanie srodowiska wirtualnego...
    call .venv\Scripts\activate.bat
) else (
    echo [INFO] Brak srodowiska wirtualnego - uzywam globalnego Python
)

echo.

echo [INFO] Uruchamianie bota...
echo [INFO] Nacisnij Ctrl+C aby zatrzymac bota
echo ====================================
echo.

if exist ".venv\Scripts\python.exe" (
    echo [INFO] Uruchamiam Python z .venv
    .venv\Scripts\python.exe main.py
) else (
    echo [INFO] Uruchamiam systemowy Python
    python main.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Bot zakonczyl dzialanie z bledem!
    echo [ERROR] Sprawdz logi powyzej
    pause
    exit /b 1
)

echo.
echo [INFO] Bot zostal zatrzymany
pause
