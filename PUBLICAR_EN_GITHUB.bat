@echo off
chcp 65001 >nul
title Publicar el buscador de noticias en internet
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publicar_en_github.ps1" %*
