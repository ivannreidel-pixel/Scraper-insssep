#!/usr/bin/env python3
"""
Genera el SITIO PUBLICABLE del buscador de noticias (para hosting gratuito, p. ej. GitHub Pages).

    python generar_sitio.py --salida site
    python generar_sitio.py --salida site --estado-previo-url https://usuario.github.io/repositorio

Qué hace:
  1. (opcional) recupera la memoria de la ejecución anterior (historial, notas ya revisadas...) desde el sitio ya publicado
  2. busca noticias (mismo motor que usa el panel en la PC)
  3. escribe en la carpeta de salida:
       index.html            el panel, en modo solo lectura
       assets/               el logo
       datos/*.json          lo que muestra el panel (estado, noticias, historial)
       estado/*.json         memoria interna para la próxima ejecución

Lo corre automáticamente .github/workflows/buscar.yml cada 3 horas.
"""

import argparse
import json
import os
import shutil
import sys
import urllib.request
from datetime import timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# Archivos de memoria que se conservan entre ejecuciones
ARCHIVOS_ESTADO = [
    "historial_noticias.json",
    "notas_revisadas.json",
    "sitios_detectados.json",
    "medios_descubiertos.json",
]
HORAS_NUEVA = 24  # en el sitio publicado, «nueva» = detectada en las últimas 24 horas


def descargar_estado_previo(url_base: str, destino: Path):
    """Baja la memoria de la ejecución anterior desde el sitio publicado. Si no existe (primera vez), se empieza de cero."""
    for nombre in ARCHIVOS_ESTADO:
        url = f"{url_base.rstrip('/')}/estado/{nombre}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "buscador-noticias"}), timeout=30) as r:
                datos = r.read()
            json.loads(datos)  # que sea un JSON válido
            (destino / nombre).write_bytes(datos)
            print(f"  ✓ memoria recuperada: {nombre} ({len(datos) // 1024} KB)")
        except Exception as e:
            print(f"  · {nombre}: no disponible ({type(e).__name__}); se empieza de cero")


def main():
    ap = argparse.ArgumentParser(description="Genera el sitio estático del buscador de noticias")
    ap.add_argument("--salida", default="site", help="carpeta donde se escribe el sitio")
    ap.add_argument("--estado-previo-url", default="", help="dirección del sitio ya publicado, para recuperar la memoria")
    ap.add_argument("--sin-buscar", action="store_true", help="no buscar: regenerar el sitio con los datos que ya existen")
    ap.add_argument("--intervalo-horas", type=int, default=int(os.environ.get("INTERVALO_HORAS", "3")),
                    help="cada cuántas horas se actualiza (solo informativo, se muestra en el sitio)")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    salida = Path(args.salida).resolve()
    estado = salida / "estado"
    datos = salida / "datos"
    for d in (estado, datos, salida / "assets"):
        d.mkdir(parents=True, exist_ok=True)

    # El motor lee y escribe sus archivos en INSSSEP_DATOS: tiene que definirse ANTES de importarlo
    os.environ["INSSSEP_DATOS"] = str(estado)
    import insssep_scraper as s  # noqa: E402

    if args.estado_previo_url and not args.sin_buscar:
        print("Recuperando la memoria de la ejecución anterior...")
        descargar_estado_previo(args.estado_previo_url, estado)

    if args.sin_buscar:
        resultado = s.InsssepScraper().obtener_ultimas_noticias()
        if not resultado.get("noticias") and not resultado.get("timestamp"):
            print("No hay datos previos para regenerar el sitio.")
            return 1
    else:
        print("Buscando noticias...")
        resultado = s.InsssepScraper().ejecutar_busqueda_completa()

    # Si casi ningún medio respondió (por ejemplo, falló la conexión del servidor), no se publica: es mejor que el
    # sitio conserve la última actualización buena que reemplazarla por una vacía.
    buscados = resultado.get("medios_buscados", 0)
    respondieron = buscados - len(resultado.get("medios_fallidos", []))
    if not args.sin_buscar and buscados and respondieron / buscados < 0.10:
        print(f"\nERROR: solo respondieron {respondieron} de {buscados} medios. No se publica esta actualización.")
        return 2

    # --- «nueva» en el sitio publicado: detectada en las últimas 24 h (no «desde la búsqueda anterior»)
    try:
        historial = json.loads(s.HISTORIAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        historial = {}
    ahora = s._ahora()
    limite = ahora - timedelta(hours=HORAS_NUEVA)
    for n in resultado["noticias"]:
        visto = (historial.get(n["url"]) or {}).get("visto")
        n["nueva"] = bool(visto) and s._a_dt(visto) >= limite
    resultado["noticias_nuevas"] = sum(1 for n in resultado["noticias"] if n["nueva"])
    resultado.pop("medios_detalle", None)  # no se usa en el sitio publicado

    # --- datos que lee el panel
    estado_json = {
        "palabras_clave": s.PALABRAS_CLAVE,
        "horas_maximas": s.HORAS_MAX,
        "coincidencia": s.COINCIDENCIA,
        "buscando": False,
        "progreso": {},
        "automatico": True,
        "intervalo_horas": args.intervalo_horas,
        "proxima_busqueda": (ahora + timedelta(hours=args.intervalo_horas)).isoformat(),
        "ultima": {
            "timestamp": resultado["timestamp"],
            "total_noticias": resultado["total_noticias"],
            "noticias_nuevas": resultado["noticias_nuevas"],
            "descartadas_antiguas": resultado.get("descartadas_antiguas", 0),
            "descartadas_sin_palabras": resultado.get("descartadas_sin_palabras", 0),
            "descartadas_sin_fecha": resultado.get("descartadas_sin_fecha", 0),
            "medios_buscados": resultado.get("medios_buscados", 0),
            "medios_fallidos": len(resultado.get("medios_fallidos", [])),
            "duracion_seg": resultado.get("duracion_seg"),
        },
        "error": None,
        "compartir": {"estado": "apagado", "url": None, "mensaje": ""},
        "puedo_compartir": False,
        "estatico": True,
        "hora_servidor": ahora.isoformat(),
    }
    items = [{"url": u, **d} for u, d in historial.items()]
    items.sort(key=lambda x: x.get("visto", ""), reverse=True)
    historial_json = {"total": len(items), "noticias": items[:200]}

    def escribir(ruta: Path, contenido):
        ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=1), encoding="utf-8")

    escribir(datos / "estado.json", estado_json)
    escribir(datos / "noticias.json", resultado)
    escribir(datos / "historial.json", historial_json)

    # --- el panel, en modo solo lectura, sin indexar en buscadores
    html = (AQUI / "dashboard.html").read_text(encoding="utf-8")
    assert "<script>" in html and "<head>" in html
    html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex, nofollow">', 1)
    html = html.replace("<script>", "<script>window.MODO_ESTATICO = true;</script>\n<script>", 1)
    (salida / "index.html").write_text(html, encoding="utf-8")
    shutil.copy(AQUI / "logo_insssep.png", salida / "assets" / "logo_insssep.png")
    (salida / ".nojekyll").write_text("", encoding="utf-8")  # GitHub Pages: servir los archivos tal cual

    if not args.sin_buscar:  # ya está en datos/noticias.json: no hace falta duplicarlo en la memoria
        (estado / "ultimas_noticias.json").unlink(missing_ok=True)

    # --- resumen
    u = estado_json["ultima"]
    print(f"\nSitio generado en {salida}")
    print(f"  Noticias: {u['total_noticias']} ({u['noticias_nuevas']} nuevas en 24 h) · "
          f"medios consultados: {u['medios_buscados'] - u['medios_fallidos']}/{u['medios_buscados']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
