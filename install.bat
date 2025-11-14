@echo off
title Instalacja Discord Music Bot
color 0B

echo ====================================
echo    Discord Music Bot - Instalacja
echo ====================================
echo.

cd /d "%~dp0"

echo [1/4] Tworzenie srodowiska wirtualnego...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Nie udalo sie stworzyc venv
    pause
    exit /b 1
)

echo [2/4] Aktywacja srodowiska...
call .venv\Scripts\activate.bat

echo [3/4] Instalowanie bibliotek...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Blad podczas instalacji bibliotek
    pause
    exit /b 1
)

echo [4/4] Sprawdzanie FFmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [UWAGA] FFmpeg nie jest zainstalowany!
    echo [INFO] Zainstaluj FFmpeg: winget install ffmpeg
) else (
    echo [OK] FFmpeg jest zainstalowany
)

echo.
echo ====================================
echo [OK] Instalacja zakonczona!
echo ====================================
echo.
echo Kolejne kroki:
echo 1. Edytuj plik .env i dodaj swoj DISCORD_TOKEN
echo 2. Uruchom bota uzywajac start_bot.bat
echo.
pause
