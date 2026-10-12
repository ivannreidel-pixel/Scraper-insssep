@echo off
chcp 65001 >nul
title Instalador INSSSEP Scraper
cd /d "%~dp0"
echo.
echo ============================================================
echo   INSTALADOR - INSSSEP SCRAPER
echo ============================================================
echo.
python --version >nul 2>nul
if errorlevel 1 (
    echo [X] Python no esta instalado en esta PC.
    echo.
    echo     1. Descargalo de https://www.python.org/downloads/
    echo     2. Al instalar, TILDA la casilla "Add python.exe to PATH"
    echo     3. Volve a abrir este instalador
    echo.
    pause
    exit /b 1
)
echo [1/2] Instalando librerias necesarias...
python -m pip install requests beautifulsoup4 apscheduler fastapi uvicorn
if errorlevel 1 (
    echo.
    echo [X] No se pudieron instalar las librerias. Revisa la conexion a internet
    echo     o pedile a sistemas que habiliten pip.
    pause
    exit /b 1
)
echo.
echo [2/2] Creando accesos directos en el Escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0crear_acceso_directo.ps1"
echo.
echo ============================================================
echo   LISTO. En el Escritorio quedo el acceso "INSSSEP Scraper".
echo   Hace doble clic para abrir el panel.
echo ============================================================
echo.
pause
