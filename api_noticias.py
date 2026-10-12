"""
INSSSEP News Scraper - Servidor + Dashboard web

Se inicia a mano (acceso directo o `python api_noticias.py`) y desde el navegador
de cualquier PC o teléfono se puede:
  - ver las noticias encontradas
  - lanzar una búsqueda ahora
  - activar / desactivar la búsqueda automática (cada N horas)
  - generar un link público para compartir el panel con otra persona

Sin PIN: cualquiera que tenga la dirección del panel puede usar los botones.
Generar o detener el link público solo se puede hacer desde la PC (o la red local), nunca desde el link público.
"""

import argparse
import atexit
import json
import re
import shutil
import socket
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from insssep_scraper import (
    BASE_DIR,
    COINCIDENCIA,
    HISTORIAL_FILE,
    HORAS_MAX,
    InsssepScraper,
    MEDIOS_CHACO,
    PALABRAS_CLAVE,
    RESULTADOS_FILE,
    logger,
)

CONFIG_FILE = BASE_DIR / "config.json"
DASHBOARD_FILE = BASE_DIR / "dashboard.html"
ASSETS = {"logo_insssep.png"}


# ---------------------------------------------------------------- configuración
def cargar_config() -> dict:
    """Lee config.json (lo crea si falta) y limpia opciones que ya no existen."""
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        cfg = {}
    cfg.setdefault("intervalo_horas", 3)
    cfg.setdefault("puerto", 8000)
    cfg.setdefault("palabras_clave", list(PALABRAS_CLAVE))
    cfg.setdefault("horas_maximas", HORAS_MAX)
    cfg.setdefault("coincidencia", COINCIDENCIA)
    cfg.pop("pin", None)  # el PIN fue eliminado
    guardar_config(cfg)
    return cfg


def guardar_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


CONFIG = cargar_config()


# ---------------------------------------------------------------- controlador de búsquedas
class Controlador:
    """Ejecuta las búsquedas (a mano o programadas) y expone su estado."""

    def __init__(self):
        self.scraper = InsssepScraper()
        self._busqueda_activa = threading.Lock()
        self._contador = threading.Lock()
        self.progreso = {"hechos": 0, "total": len(MEDIOS_CHACO), "ultimo": "", "origen": ""}
        self.buscando = False
        self.error: Optional[str] = None
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    # --- búsquedas
    def buscar(self, origen: str = "manual") -> bool:
        """Lanza una búsqueda en segundo plano. False si ya hay una en curso."""
        if not self._busqueda_activa.acquire(blocking=False):
            return False
        self.progreso.update(hechos=0, ultimo="", origen=origen, total=self.scraper.total_medios())
        self.buscando = True
        threading.Thread(target=self._correr, daemon=True).start()
        return True

    def _correr(self):
        try:
            self.error = None
            self.scraper.ejecutar_busqueda_completa(on_progress=self._avance)
        except Exception as e:
            self.error = str(e)
            logger.exception("Error en la búsqueda")
        finally:
            self.buscando = False
            self._busqueda_activa.release()

    def _avance(self, medio: dict, cantidad: int):
        with self._contador:
            self.progreso["hechos"] += 1
            self.progreso["ultimo"] = medio["nombre"]

    # --- modo automático
    def _tarea_programada(self):
        self.buscar(origen="automática")

    def set_automatico(self, activo: bool, horas: int):
        if self.scheduler.get_job("auto"):
            self.scheduler.remove_job("auto")
        if activo:
            self.scheduler.add_job(
                self._tarea_programada, "interval", hours=horas, id="auto",
                max_instances=1, next_run_time=datetime.now().astimezone() + timedelta(hours=horas),
            )
            logger.info(f"Modo automático ACTIVADO (cada {horas} h)")
        else:
            logger.info("Modo automático DESACTIVADO")

    @property
    def automatico(self) -> bool:
        return self.scheduler.get_job("auto") is not None

    @property
    def proxima(self) -> Optional[str]:
        job = self.scheduler.get_job("auto")
        return job.next_run_time.isoformat() if job and job.next_run_time else None


ctrl = Controlador()


# ---------------------------------------------------------------- link público (túnel Cloudflare)
class Tunel:
    """Publica el panel en internet con un túnel gratuito de Cloudflare (sin cuenta)."""

    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self.estado = "apagado"  # apagado | iniciando | listo | error
        self.url: Optional[str] = None
        self.mensaje = ""
        self.puerto = CONFIG["puerto"]
        atexit.register(self.detener)

    @staticmethod
    def _buscar_exe() -> Optional[str]:
        ruta = shutil.which("cloudflared")
        if ruta:
            return ruta
        for p in (r"C:\Program Files (x86)\cloudflared\cloudflared.exe", r"C:\Program Files\cloudflared\cloudflared.exe"):
            if Path(p).exists():
                return p
        return None

    def iniciar(self) -> bool:
        if self.estado in ("iniciando", "listo"):
            return True
        exe = self._buscar_exe()
        if not exe:
            self.estado, self.url = "error", None
            self.mensaje = ("Falta instalar 'cloudflared' (gratis). En PowerShell: "
                            "winget install --id Cloudflare.cloudflared  y volver a abrir el programa.")
            return False
        self.estado, self.url, self.mensaje = "iniciando", None, ""
        self.proc = subprocess.Popen(
            [exe, "tunnel", "--url", f"http://localhost:{self.puerto}", "--no-autoupdate"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        proc = self.proc
        threading.Thread(target=self._leer, args=(proc,), daemon=True).start()
        threading.Timer(45, self._vencio, args=(proc,)).start()
        return True

    def _leer(self, proc):
        for linea in proc.stderr:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", linea)
            if m and proc is self.proc and self.estado == "iniciando":
                self.url, self.estado = m.group(0), "listo"
                print(f"\n  🌍 LINK PARA COMPARTIR (funciona desde cualquier red):\n     {self.url}\n")
        if proc is self.proc and self.estado != "apagado":  # el túnel se cortó solo
            self.estado, self.url, self.mensaje = "error", None, "El link público se cortó. Generalo de nuevo."

    def _vencio(self, proc):
        if proc is self.proc and self.estado == "iniciando":
            self.detener()
            self.estado, self.mensaje = "error", "No se pudo crear el link (¿hay internet?). Probá de nuevo."

    def detener(self):
        proc, self.proc = self.proc, None
        self.estado, self.url = "apagado", None
        if proc and proc.poll() is None:
            proc.terminate()

    def resumen(self) -> dict:
        return {"estado": self.estado, "url": self.url, "mensaje": self.mensaje}


tunel = Tunel()


# ---------------------------------------------------------------- utilidades
_cache = {"mtime": None, "datos": None}


def leer_ultimo() -> Optional[dict]:
    """Último resultado guardado (con caché por fecha de modificación)."""
    try:
        mtime = RESULTADOS_FILE.stat().st_mtime
    except FileNotFoundError:
        return None
    if _cache["mtime"] != mtime:
        try:
            _cache["datos"] = json.loads(RESULTADOS_FILE.read_text(encoding="utf-8"))
            _cache["mtime"] = mtime
        except Exception:
            return _cache["datos"]
    return _cache["datos"]


def es_local(request: Request) -> bool:
    """True si la visita llega directo (esta PC o la red local) y no por el link público de Cloudflare."""
    h = request.headers
    return not any(k in h for k in ("cf-connecting-ip", "cf-ray", "x-forwarded-for"))


# ---------------------------------------------------------------- API
app = FastAPI(title="INSSSEP News Scraper", version="3.0.0")


class OrdenAutomatico(BaseModel):
    activo: bool
    horas: Optional[int] = None


class OrdenCompartir(BaseModel):
    activo: bool


class ResultadoRemoto(BaseModel):
    """Formato que envía insssep_scraper_con_api.py (modo servidor remoto)."""
    model_config = {"extra": "allow"}
    timestamp: str
    palabra_clave: str
    total_noticias: int
    medios_buscados: int
    noticias: List[dict]


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(DASHBOARD_FILE, media_type="text/html", headers={"Cache-Control": "no-cache"})


@app.get("/assets/{nombre}", include_in_schema=False)
def asset(nombre: str):
    """Sirve solo los archivos de imagen del panel (lista cerrada)."""
    if nombre not in ASSETS:
        raise HTTPException(status_code=404)
    return FileResponse(BASE_DIR / nombre, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/estado")
def estado(request: Request):
    ultimo = leer_ultimo()
    resumen = None
    if ultimo:
        resumen = {
            "timestamp": ultimo.get("timestamp"),
            "total_noticias": ultimo.get("total_noticias", 0),
            "noticias_nuevas": ultimo.get("noticias_nuevas", 0),
            "descartadas_antiguas": ultimo.get("descartadas_antiguas", 0),
            "descartadas_sin_palabras": ultimo.get("descartadas_sin_palabras", 0),
            "descartadas_sin_fecha": ultimo.get("descartadas_sin_fecha", 0),
            "medios_buscados": ultimo.get("medios_buscados", 0),
            "medios_fallidos": len(ultimo.get("medios_fallidos", [])),
            "duracion_seg": ultimo.get("duracion_seg"),
        }
    return {
        "palabras_clave": PALABRAS_CLAVE,
        "horas_maximas": HORAS_MAX,
        "coincidencia": COINCIDENCIA,
        "buscando": ctrl.buscando,
        "progreso": ctrl.progreso,
        "automatico": ctrl.automatico,
        "intervalo_horas": CONFIG["intervalo_horas"],
        "proxima_busqueda": ctrl.proxima,
        "ultima": resumen,
        "error": ctrl.error,
        "compartir": tunel.resumen(),
        "puedo_compartir": es_local(request),
        "hora_servidor": datetime.now().astimezone().isoformat(),
    }


@app.get("/api/noticias")
def noticias(limite: Optional[int] = None):
    datos = leer_ultimo() or {"noticias": [], "total_noticias": 0}
    if limite:
        datos = {**datos, "noticias": datos["noticias"][:limite]}
    return datos


@app.get("/api/historial")
def historial(limite: int = 200):
    """Todas las noticias vistas alguna vez (últimos 30 días), la más reciente primero."""
    try:
        h = json.loads(HISTORIAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        h = {}
    items = [{"url": u, **d} for u, d in h.items()]
    items.sort(key=lambda x: x.get("visto", ""), reverse=True)
    return {"total": len(items), "noticias": items[:max(1, min(limite, 1000))]}


@app.post("/api/buscar")
def buscar_ahora():
    if not ctrl.buscar(origen="manual"):
        raise HTTPException(status_code=409, detail="Ya hay una búsqueda en curso")
    return {"ok": True}


@app.post("/api/automatico")
def automatico(orden: OrdenAutomatico):
    horas = orden.horas or CONFIG["intervalo_horas"]
    horas = max(1, min(int(horas), 24))
    CONFIG["intervalo_horas"] = horas
    guardar_config(CONFIG)
    ctrl.set_automatico(orden.activo, horas)
    return {"ok": True, "automatico": ctrl.automatico, "intervalo_horas": horas}


@app.post("/api/compartir")
def compartir(orden: OrdenCompartir, request: Request):
    """Genera o detiene el link público. Solo desde la PC / red local, no desde el propio link público."""
    if not es_local(request):
        raise HTTPException(status_code=403, detail="Esto solo se puede hacer desde la PC donde corre el programa")
    if orden.activo:
        tunel.iniciar()
    else:
        tunel.detener()
    return tunel.resumen()


@app.post("/api/noticias/recibir")
def recibir_noticias(resultado: ResultadoRemoto, request: Request):
    """Modo servidor remoto: recibe lo que envía insssep_scraper_con_api.py (solo red local)."""
    if not es_local(request):
        raise HTTPException(status_code=403, detail="No permitido desde el link público")
    datos = resultado.model_dump()
    RESULTADOS_FILE.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "success", "mensaje": f"Recibidas {resultado.total_noticias} noticias"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------- arranque
def ip_local() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # UDP: no envía nada, solo elige la interfaz
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def puerto_libre(puerto: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", puerto)) != 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Dashboard INSSSEP")
    parser.add_argument("--port", type=int, default=CONFIG["puerto"])
    parser.add_argument("--sin-navegador", action="store_true", help="no abrir el navegador al iniciar")
    parser.add_argument("--publico", action="store_true", help="generar el link público apenas inicia")
    args = parser.parse_args()
    tunel.puerto = args.port

    url_local = f"http://localhost:{args.port}"
    if not puerto_libre(args.port):
        print(f"\nEl panel ya está abierto en {url_local}. Abriéndolo...")
        if not args.sin_navegador:
            webbrowser.open(url_local)
        return

    ip = ip_local()
    print("\n" + "=" * 62)
    print("  INSSSEP NEWS SCRAPER - PANEL DE CONTROL")
    print("=" * 62)
    print(f"\n  En esta PC:           {url_local}")
    print(f"  Desde otro equipo:    http://{ip}:{args.port}   (misma red Wi-Fi)")
    print("\n  Para generar un link para otra persona: botón «Generar link» del panel.")
    print("  Para APAGAR: cerrá esta ventana (o Ctrl+C).")
    print("=" * 62 + "\n")

    if args.publico:
        if not tunel.iniciar():
            print(f"  ⚠ {tunel.mensaje}\n")
    if not args.sin_navegador:
        threading.Timer(1.5, lambda: webbrowser.open(url_local)).start()

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPanel detenido.")
