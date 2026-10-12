@echo off
chcp 65001 >nul
title INSSSEP Scraper - Panel de control
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python api_noticias.py %*
if errorlevel 1 (
    echo.
    echo Ocurrio un error. Si dice "No module named", ejecuta:  pip install -r requirements.txt
    pause
)
