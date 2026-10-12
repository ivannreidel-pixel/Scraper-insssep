#!/bin/bash

# INSSSEP News Scraper - Quick Start
# Ejecutar: bash quickstart.sh

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     INSSSEP NEWS SCRAPER - QUICK START 🚀                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Crear entorno virtual
echo "1️⃣  Creando entorno virtual..."
python3 -m venv venv

# Activar
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Instalar dependencias
echo ""
echo "2️⃣  Instalando dependencias..."
pip install -q -r requirements.txt

# Listo
echo ""
echo "✅ ¡LISTO!"
echo ""
echo "Ahora ejecuta en DOS terminales diferentes:"
echo ""
echo "Terminal 1 (Scraper):"
echo "  python insssep_scraper.py"
echo ""
echo "Terminal 2 (Dashboard):"
echo "  python api_noticias.py"
echo ""
echo "Luego abre tu navegador:"
echo "  http://localhost:8000"
echo ""
