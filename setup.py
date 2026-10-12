#!/usr/bin/env python3
"""
Script de instalación y configuración para INSSSEP News Scraper
Ejecutar: python setup.py
"""

import os
import sys
import json
from pathlib import Path

def crear_config():
    """Crea archivo de configuración interactivo"""
    print("\n" + "="*60)
    print("🚀 CONFIGURACIÓN INSSSEP NEWS SCRAPER")
    print("="*60 + "\n")
    
    config = {
        "modo": "local",
        "intervalo_horas": 3,
        "puerto": 8000,
        "palabras_clave": ["INSSSEP", "Rafael Meneses"],
        "horas_maximas": 72,
        "coincidencia": "cualquiera",  # basta que la nota mencione una de las palabras clave
        "guardar_localmente": True,
        "servidor_remoto": None
    }
    
    print("1️⃣  MODO DE OPERACIÓN")
    print("   [1] Local (solo en tu PC)")
    print("   [2] Remoto (PC + Servidor en nube)")
    
    modo = input("\nElige opción (1 o 2): ").strip()
    
    if modo == "1":
        config["modo"] = "local"
    elif modo == "2":
        config["modo"] = "remoto"
        servidor = input("URL del servidor remoto (ej: http://tu-app.herokuapp.com): ").strip()
        if servidor:
            config["servidor_remoto"] = servidor
    
    print("\n2️⃣  INTERVALO DE BÚSQUEDA")
    print("   [Actual: 3 horas]")
    intervalo = input("Cambiar a X horas (o presiona Enter para mantener): ").strip()
    if intervalo and intervalo.isdigit():
        config["intervalo_horas"] = int(intervalo)
    
    print("\n3️⃣  PALABRAS CLAVE")
    print("   [Actual: INSSSEP, Rafael Meneses]")
    palabras = input("Cambiar (separadas por coma) o presiona Enter para mantener: ").strip()
    if palabras:
        config["palabras_clave"] = [p.strip() for p in palabras.split(",") if p.strip()]
    
    print("\n4️⃣  PUERTO LOCAL")
    print("   [Actual: 8000]")
    puerto = input("Cambiar a puerto (o presiona Enter para mantener): ").strip()
    if puerto and puerto.isdigit():
        config["puerto"] = int(puerto)
    
    # Guardar configuración
    config_file = Path("config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("✅ CONFIGURACIÓN GUARDADA")
    print("="*60)
    print(f"\nModo: {config['modo'].upper()}")
    print(f"Intervalo: {config['intervalo_horas']} horas")
    print(f"Palabras clave: {', '.join(config['palabras_clave'])}")
    print(f"Antigüedad máxima de las noticias: {config['horas_maximas']} horas")
    print(f"Puerto: {config['puerto']}")
    if config["servidor_remoto"]:
        print(f"Servidor: {config['servidor_remoto']}")
    
    return config


def mostrar_proximos_pasos(config):
    """Muestra instrucciones de cómo ejecutar"""
    print("\n" + "="*60)
    print("📝 PRÓXIMOS PASOS")
    print("="*60 + "\n")
    
    print("1️⃣  Crear el acceso directo en el Escritorio (PowerShell):")
    print("   .\\crear_acceso_directo.ps1")

    print("\n2️⃣  Abrir el panel (doble clic en el acceso directo, o):")
    print(f"   python api_noticias.py --port {config['puerto']}")

    print(f"\n3️⃣  Desde esta PC:  http://localhost:{config['puerto']}")
    print("    Desde otro equipo: la dirección que muestra la ventana negra (misma red Wi-Fi)")
    print("    Para compartirlo con otra persona: botón «Generar link» del panel")

    print("\n4️⃣  Para apagar: cerrar la ventana negra")

    if config["modo"] == "remoto":
        print("\n(Modo remoto) Para enviar resultados a un servidor:")
        print(f"   python scraper_manual.py {config['servidor_remoto']}")
    
    print("\n" + "="*60 + "\n")


def verificar_dependencias():
    """Verifica si están instaladas las dependencias"""
    print("\n📦 Verificando dependencias...\n")
    
    dependencias_requeridas = [
        'requests',
        'bs4',
        'apscheduler',
        'fastapi',
        'uvicorn'
    ]
    
    faltantes = []
    
    for dep in dependencias_requeridas:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep}")
            faltantes.append(dep)
    
    if faltantes:
        print(f"\n⚠️  Faltan {len(faltantes)} dependencia(s)")
        print("\nInstalar con:")
        print("   pip install -r requirements.txt")
        return False
    
    print("\n✅ Todas las dependencias están instaladas")
    return True


def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     INSSSEP NEWS SCRAPER - INSTALLATION WIZARD 🚀         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Verificar dependencias
    if not verificar_dependencias():
        return
    
    # Crear configuración
    config = crear_config()
    
    # Mostrar próximos pasos
    mostrar_proximos_pasos(config)
    
    print("💡 TIPS:")
    print("   • Ejecuta ambas terminales en paralelo (split screen)")
    print("   • Los logs te mostrarán cada búsqueda completada")
    print("   • Presiona Ctrl+C para detener cualquiera")
    print("   • El dashboard se actualiza automáticamente cada 30 seg")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuración cancelada")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
