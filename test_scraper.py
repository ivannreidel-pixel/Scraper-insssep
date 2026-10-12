#!/usr/bin/env python3
"""
Test script para INSSSEP News Scraper
Verifica que todo funciona correctamente
Ejecutar: python test_scraper.py
"""

import sys
import time
from pathlib import Path

# Colores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test(nombre, funcion):
    """Ejecuta un test"""
    print(f"\n{BLUE}🧪 Test: {nombre}{RESET}")
    try:
        resultado = funcion()
        if resultado:
            print(f"{GREEN}✅ PASS{RESET}")
            return True
        else:
            print(f"{RED}❌ FAIL{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ ERROR: {e}{RESET}")
        return False


def test_importes():
    """Verifica que todas las librerías están instaladas"""
    librerias = {
        'requests': 'requests',
        'BeautifulSoup': 'bs4',
        'APScheduler': 'apscheduler',
        'FastAPI': 'fastapi',
        'uvicorn': 'uvicorn'
    }
    
    print("  Verificando importes...")
    for nombre, modulo in librerias.items():
        try:
            __import__(modulo)
            print(f"    ✓ {nombre}")
        except ImportError:
            print(f"    ✗ {nombre} - FALTA")
            return False
    
    return True


def test_scraper_basico():
    """Test básico de scraping"""
    print("  Intentando conectar a Diario Chaco...")
    
    import requests
    from bs4 import BeautifulSoup
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get('https://www.diariochaco.com', 
                               headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            enlaces = soup.find_all('a')
            print(f"    ✓ Conectado. Encontrados {len(enlaces)} enlaces")
            return True
        else:
            print(f"    ✗ Status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("    ⚠ Timeout (conexión lenta)")
        return False
    except Exception as e:
        print(f"    ✗ Error: {str(e)[:50]}")
        return False


def test_scheduler():
    """Verifica que APScheduler funciona"""
    print("  Configurando scheduler por 3 segundos...")
    
    from apscheduler.schedulers.background import BackgroundScheduler
    
    try:
        contador = {'valor': 0}
        
        def tarea():
            contador['valor'] += 1
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(tarea, 'interval', seconds=1, id='test')
        scheduler.start()
        
        time.sleep(3.5)
        scheduler.shutdown()
        
        if contador['valor'] >= 3:
            print(f"    ✓ Ejecutada {contador['valor']} veces")
            return True
        else:
            print(f"    ✗ Solo ejecutada {contador['valor']} veces")
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False


def test_json_escritura():
    """Verifica que pueda escribir JSON"""
    print("  Escribiendo archivo de prueba...")
    
    import json
    
    try:
        test_file = Path('test_noticias.json')
        test_data = {
            'noticias': [
                {'titulo': 'Test', 'url': 'http://test.com'}
            ]
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Leer de vuelta
        with open(test_file, 'r', encoding='utf-8') as f:
            datos_leidos = json.load(f)
        
        # Limpiar
        test_file.unlink()
        
        if datos_leidos['noticias'][0]['titulo'] == 'Test':
            print("    ✓ JSON escrito y leído correctamente")
            return True
        else:
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False


def test_fastapi_basico():
    """Verifica que FastAPI puede arrancar"""
    print("  Verificando FastAPI...")
    
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse
        
        app = FastAPI()
        
        @app.get("/")
        async def root():
            return {"status": "ok"}
        
        print("    ✓ FastAPI cargado correctamente")
        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False


def test_estructura_archivos():
    """Verifica que existan todos los archivos necesarios"""
    print("  Verificando archivos...")
    
    archivos_requeridos = [
        'insssep_scraper.py',
        'insssep_scraper_con_api.py',
        'scraper_manual.py',
        'medios.py',
        'dashboard.html',
        'logo_insssep.png',
        'INSSSEP.bat',
        'api_noticias.py',
        'generar_sitio.py',
        '.github/workflows/buscar.yml',
        'requirements.txt',
        'README.md'
    ]
    
    todos_ok = True
    for archivo in archivos_requeridos:
        existe = Path(archivo).exists()
        simbolo = "✓" if existe else "✗"
        print(f"    {simbolo} {archivo}")
        if not existe:
            todos_ok = False
    
    return todos_ok


def test_medios_chaco():
    """Verifica conectividad con medios locales"""
    print("  Verificando medios locales de Chaco...")
    
    import requests
    
    medios = {
        'Diario Chaco': 'https://www.diariochaco.com',
        'Chaco Día por Día': 'https://chacodiapordia.com',
    }
    
    accesibles = 0
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for nombre, url in medios.items():
        try:
            response = requests.head(url, headers=headers, timeout=5)
            if response.status_code < 400:
                print(f"    ✓ {nombre}")
                accesibles += 1
            else:
                print(f"    ⚠ {nombre} (status {response.status_code})")
        except Exception as e:
            print(f"    ✗ {nombre} ({str(e)[:30]})")
    
    return accesibles >= 1


def main():
    print("\n" + "="*60)
    print(f"{BLUE}🧪 INSSSEP NEWS SCRAPER - TEST SUITE{RESET}")
    print("="*60 + "\n")
    
    tests = [
        ("Importes Python", test_importes),
        ("Estructura de archivos", test_estructura_archivos),
        ("JSON escritura/lectura", test_json_escritura),
        ("FastAPI básico", test_fastapi_basico),
        ("Scheduler (APScheduler)", test_scheduler),
        ("Conectividad con medios", test_medios_chaco),
        ("Scraper básico", test_scraper_basico),
    ]
    
    resultados = []
    for nombre, func in tests:
        resultados.append(test(nombre, func))
    
    # Resumen
    print("\n" + "="*60)
    print(f"{BLUE}📊 RESUMEN{RESET}")
    print("="*60)
    
    pasaron = sum(resultados)
    total = len(resultados)
    
    print(f"\nTests pasados: {pasaron}/{total}")
    
    if pasaron == total:
        print(f"\n{GREEN}✅ ¡TODOS LOS TESTS PASARON!{RESET}")
        print("\n🚀 Estás listo para ejecutar:")
        print("   • INSSSEP.bat  (o: python api_noticias.py)")
        return 0
    else:
        print(f"\n{YELLOW}⚠️  {total - pasaron} test(s) fallaron{RESET}")
        print("\nSoluciona los errores arriba antes de ejecutar")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{RED}❌ Tests interrumpidos{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error fatal: {e}{RESET}\n")
        sys.exit(1)
