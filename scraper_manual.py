#!/usr/bin/env python3
"""
INSSSEP News Scraper - Búsqueda MANUAL
Busca INMEDIATAMENTE (sin esperar al scheduler), muestra resultados en consola
y guarda en ultimas_noticias.json.

Uso:
    python scraper_manual.py
    python scraper_manual.py http://servidor-remoto.com   # además envía al servidor
"""

import sys
import json
from datetime import datetime

import requests

from insssep_scraper import InsssepScraper, PALABRA_CLAVE, RESULTADOS_FILE
from medios import MEDIOS_CHACO


def enviar_a_servidor(servidor: str, resultado: dict) -> bool:
    """Envía el resultado al servidor remoto (mismo endpoint que insssep_scraper_con_api)"""
    endpoint = f"{servidor.rstrip('/')}/api/noticias/recibir"
    try:
        r = requests.post(endpoint, json=resultado, timeout=15)
        if r.status_code == 200:
            print(f"✓ Enviado a {servidor}")
            return True
        print(f"⚠ El servidor respondió {r.status_code}: {r.text[:100]}")
    except requests.exceptions.RequestException as e:
        print(f"⚠ No se pudo conectar a {servidor}: {str(e)[:80]}")
    return False


def main() -> int:
    servidor = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print(f"🔎 BÚSQUEDA MANUAL '{PALABRA_CLAVE}' - {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 60)

    scraper = InsssepScraper()
    print(f"Consultando {scraper.total_medios()} medios en paralelo (la primera vez tarda unos 2-3 minutos)...\n")
    resultado = scraper.ejecutar_busqueda_completa()
    todas = resultado["noticias"]
    nuevas = [n for n in todas if n["nueva"]]
    conteo = {m["nombre"]: m["noticias"] for m in resultado["medios_detalle"]}

    print("\n" + "=" * 60)
    print("📊 RESULTADOS POR MEDIO")
    print("=" * 60)
    con_noticias = {k: v for k, v in conteo.items() if v}
    for nombre, n in sorted(con_noticias.items(), key=lambda x: -x[1]):
        print(f"  {nombre:<32} {n} noticia(s)")
    if not con_noticias:
        print("  (ningún medio publicó noticias con la palabra clave)")

    total_medios = resultado["medios_buscados"]
    ok = total_medios - len(scraper.fallidos)
    print(f"\n  TOTAL: {len(todas)} noticia(s) de las últimas {resultado['horas_maximas']} h "
          f"({len(nuevas)} nuevas desde la última búsqueda)")
    solo_una = (f" · por mencionar solo una de las palabras: {resultado['descartadas_sin_palabras']}"
                if resultado['coincidencia'] == 'todas' else "")
    print(f"  Descartadas por antiguas: {resultado['descartadas_antiguas']}{solo_una} · "
          f"por no poder comprobar su fecha: {resultado['descartadas_sin_fecha']}")
    print(f"  Medios consultados OK: {ok}/{total_medios} "
          f"(sin noticias: {ok - len(con_noticias)}, con noticias: {len(con_noticias)})")
    if scraper.fallidos:
        print(f"  ⚠ No respondieron ({len(scraper.fallidos)}): {', '.join(sorted(scraper.fallidos))}")
    if todas:
        print("\n📰 NOTICIAS")
        for n in todas:
            marca = "🆕 " if n['nueva'] else ""
            fecha = datetime.fromisoformat(n['publicada']).strftime("%d/%m %H:%M")
            print(f"  • {marca}[{n['medio']}] {n['titulo']}\n    {'+'.join(n['palabras'])} · publicada: {fecha}\n    {n['url']}")

    print(f"\n💾 Guardado en {RESULTADOS_FILE.resolve()}")

    if servidor:
        enviar_a_servidor(servidor, resultado)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nBúsqueda cancelada")
        sys.exit(1)
