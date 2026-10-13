"""
INSSSEP News Scraper
Busca noticias que mencionen las palabras clave (INSSSEP, Rafael Meneses) en medios locales de Chaco.
Solo conserva las publicadas en las últimas 72 horas.
Ejecutable localmente cada 3 horas
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import calendar
import json
import os
import re
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Dict, List, Optional, Tuple
import time
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler

from medios import MEDIOS_CHACO

BASE_DIR = Path(__file__).resolve().parent
# Carpeta donde se guardan los datos generados (resultados, historial, cachés). Por defecto, junto al programa;
# en el servidor se redirige con la variable de entorno INSSSEP_DATOS.
DATA_DIR = Path(os.environ.get("INSSSEP_DATOS") or BASE_DIR)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configurar logging (consola + scraper.log, para cuando corre sin ventana)
_handlers = [RotatingFileHandler(BASE_DIR / "scraper.log", maxBytes=500_000, backupCount=1, encoding="utf-8")]  # máx. ~1 MB en total
if sys.stderr is not None:
    _handlers.append(logging.StreamHandler())
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=_handlers
)
logger = logging.getLogger(__name__)


def _leer_config() -> dict:
    try:
        return json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


_cfg = _leer_config()

# Palabras clave (se pueden cambiar en config.json -> "palabras_clave")
PALABRAS_CLAVE: List[str] = [p.strip() for p in _cfg.get("palabras_clave", ["INSSSEP", "Rafael Meneses"]) if p.strip()]
PALABRA_CLAVE = " / ".join(PALABRAS_CLAVE)  # para mostrar
# Otras formas de nombrar lo mismo (config.json -> "sinonimos"). Se buscan igual que la palabra clave y cuentan como ella.
SINONIMOS: Dict[str, List[str]] = _cfg.get("sinonimos", {"INSSSEP": [
    "Instituto de Seguridad Social, Seguros y Préstamos", "Instituto de Seguridad Social, Seguros y Prestamos"]})
TERMINOS: Dict[str, List[str]] = {p: [p] + list(SINONIMOS.get(p, [])) for p in PALABRAS_CLAVE}


def _patron(terminos):
    """Coincide con la palabra o frase completa, sin importar mayúsculas ni espacios de más (InSSSeP, Rafael  Meneses...)"""
    alt = '|'.join(r'\s+'.join(re.escape(x) for x in t.split()) for t in terminos)
    return re.compile(r'(?<!\w)(?:' + alt + r')(?!\w)', re.IGNORECASE)


_PATRONES = {p: _patron(TERMINOS[p]) for p in PALABRAS_CLAVE}

# "cualquiera": basta con que la nota mencione UNA de las palabras clave (INSSSEP o Rafael Meneses).
# "todas": la nota debe mencionarlas todas. (config.json -> "coincidencia")
COINCIDENCIA = _cfg.get("coincidencia", "cualquiera")

# Antigüedad máxima de una noticia, en horas (config.json -> "horas_maximas")
HORAS_MAX = int(_cfg.get("horas_maximas", 72))

MAX_HILOS = 10          # medios consultados en paralelo
MAX_NOTAS_NUEVAS_POR_MEDIO = 80  # tope de notas nuevas que se abren por medio en cada búsqueda

RESULTADOS_FILE = DATA_DIR / "ultimas_noticias.json"
HISTORIAL_FILE = DATA_DIR / "historial_noticias.json"  # URLs ya vistas
HISTORIAL_DIAS = 30  # cuánto se recuerda una noticia vista
CACHE_FILE = DATA_DIR / "notas_revisadas.json"  # notas ya abiertas (para no repetir el trabajo)
CACHE_DIAS = 6
SITIOS_FILE = DATA_DIR / "sitios_detectados.json"  # qué sitios son WordPress / tienen feed (se recuerda unos días)
SITIOS_DIAS = 7
DESCUBIERTOS_FILE = DATA_DIR / "medios_descubiertos.json"  # medios nuevos que fue mostrando Google Noticias
MAX_DESCUBIERTOS = 40
FEEDS_COMUNES = ["/feed", "/rss", "/rss.xml", "/?feed=rss2", "/feed.xml", "/atom.xml", "/feeds/posts/default"]

# Zona horaria de Argentina (UTC-3, sin horario de verano). Es fija para que las fechas sean iguales en tu PC y en un
# servidor que funcione en otra zona. (config.json -> "zona_horaria" en horas, por si hiciera falta)
_TZ = timezone(timedelta(hours=float(_cfg.get("zona_horaria", -3))), "ART")


def _ahora() -> datetime:
    return datetime.now(_TZ)


def _a_dt(iso: str) -> datetime:
    """Fecha guardada como texto -> datetime con zona (las guardadas sin zona se toman en hora de Argentina)."""
    dt = datetime.fromisoformat(iso)
    return dt if dt.tzinfo else dt.replace(tzinfo=_TZ)


def _norm(texto: str) -> str:
    """Título normalizado para detectar la misma nota publicada por varias fuentes."""
    return re.sub(r'\W+', ' ', texto.lower()).strip()


def _parsear_fecha(texto: str) -> Optional[datetime]:
    """Interpreta fechas ISO (con o sin zona horaria) y dd/mm/aaaa. Devuelve datetime con zona."""
    s = (texto or "").strip().replace("Z", "+00:00")
    if not s:
        return None
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s)  # solo día: se toma el mediodía
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return datetime(y, mo, d, 12, 0, 0, tzinfo=_TZ)
        except ValueError:
            return None
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
        if not m:
            return None
        d, mo, y = map(int, m.groups())
        try:
            return datetime(y, mo, d, 12, 0, 0, tzinfo=_TZ)
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=_TZ)


_MESES = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
          'septiembre': 9, 'setiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
          'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
          'sep': 9, 'set': 9, 'oct': 10, 'nov': 11, 'dic': 12}
_MES = '(' + '|'.join(sorted(_MESES, key=len, reverse=True)) + ')'
# "24 septiembre, 2026" · "29 de septiembre de 2026" · "29 sep"
_RE_DIA_MES = re.compile(r'(?<!\d)(\d{1,2})\s*(?:de\s+)?' + _MES + r'\b\.?,?(?:\s*(?:de\s+)?(20\d{2}))?', re.I)
# "octubre 2, 2026"
_RE_MES_DIA = re.compile(_MES + r'\b\.?\s+(\d{1,2}),?\s+(20\d{2})', re.I)
# "24/09/2026"
_RE_NUM = re.compile(r'(?<!\d)(\d{1,2})[/-](\d{1,2})[/-](20\d{2}|\d{2})(?!\d)')
# "hace 3 horas"
_RE_HACE = re.compile(r'hace\s+(\d+)\s+(minutos?|min|horas?|hs|d[ií]as?)\b', re.I)
_RE_HORA = re.compile(r'(?<!\d)(\d{1,2}):(\d{2})\s*([ap])?\.?\s*m?\.?', re.I)


def _fecha_en_texto(texto: str) -> Optional[datetime]:
    """
    Busca la fecha de publicación escrita a la vista, cerca del título ("24 septiembre, 2026 11:19 am",
    "hace 3 horas", "29/09/2026"...). Sin hora se toma el mediodía; sin año, el año en curso.
    """
    m = _RE_HACE.search(texto)
    if m:
        n, unidad = int(m.group(1)), m.group(2).lower()
        delta = (timedelta(minutes=n) if unidad.startswith('min') else
                 timedelta(hours=n) if unidad[0] == 'h' else timedelta(days=n))
        return _ahora() - delta

    candidatos = []  # (posición, año, mes, día, fin_del_match)
    for m in _RE_DIA_MES.finditer(texto):
        d, mes, a = int(m.group(1)), _MESES[m.group(2).lower()], m.group(3)
        candidatos.append((m.start(), int(a) if a else None, mes, d, m.end()))
    for m in _RE_MES_DIA.finditer(texto):
        candidatos.append((m.start(), int(m.group(3)), _MESES[m.group(1).lower()], int(m.group(2)), m.end()))
    for m in _RE_NUM.finditer(texto):
        anio_n = int(m.group(3))
        candidatos.append((m.start(), anio_n + 2000 if anio_n < 100 else anio_n, int(m.group(2)), int(m.group(1)), m.end()))
    if not candidatos:
        return None

    _, anio, mes, dia, fin = min(candidatos)  # la primera que aparece junto al título
    hoy = _ahora()
    try:
        if anio is None:
            anio = hoy.year
            if datetime(anio, mes, dia, tzinfo=_TZ) > hoy + timedelta(days=2):  # "29 dic" visto en enero
                anio -= 1
        hora, minuto = 12, 0
        h = _RE_HORA.match(texto[fin:fin + 25].lstrip(' ,-·|'))
        if h:
            hora, minuto = int(h.group(1)), int(h.group(2))
            if h.group(3):
                pm = h.group(3).lower() == 'p'
                hora = hora % 12 + (12 if pm else 0)
        return datetime(anio, mes, dia, hora % 24, minuto, tzinfo=_TZ)
    except ValueError:
        return None


def _fecha_desde_url(url: str) -> Tuple[Optional[datetime], bool]:
    """
    Fecha que aparece en la dirección (/2026/09/28/...).
    Retorna (fecha_más_tardía_posible, es_exacta). Si solo trae año/mes, no es exacta.
    """
    try:
        m = re.search(r'-(20\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})(?:$|[/?#.])', url)  # ...-2026-10-01-21-46 (con hora)
        if m:
            y, mo, d, h, mi = map(int, m.groups())
            return datetime(y, mo, d, h, mi, tzinfo=_TZ), True
        m = re.search(r'/(20\d{2})/(\d{1,2})/(\d{1,2})(?=[/\-_.]|$)', url)
        if m:
            y, mo, d = map(int, m.groups())
            return datetime(y, mo, d, 12, 0, 0, tzinfo=_TZ), True
        m = re.search(r'/(20\d{2})/(\d{1,2})(?=/)', url)
        if m:
            y, mo = map(int, m.groups())
            return datetime(y, mo, calendar.monthrange(y, mo)[1], 23, 59, 59, tzinfo=_TZ), False
    except ValueError:
        pass
    return None, False


class InsssepScraper:
    """
    Busca notas que mencionen las palabras clave, publicadas en las últimas HORAS_MAX horas.
    Usa varias fuentes que se complementan:
      1. Buscador interno de los sitios WordPress (API REST): encuentra notas aunque ya no estén en la portada
         y trae fecha y texto completos.
      2. Feed RSS/Atom de los demás sitios: fecha exacta de publicación y, a veces, el texto completo.
      3. Notas de la portada (con caché, para no reabrir lo ya revisado).
      4. Google Noticias (RSS): notas de otros medios; los medios nuevos que aparecen se agregan solos
         a la lista para consultarlos directamente la próxima vez.
    """

    def __init__(self):
        self.resultados = []
        self.fallidos = {}  # {medio: motivo} de los que no respondieron en la última búsqueda
        self.descartadas = 0  # notas con las palabras clave pero de más de HORAS_MAX horas
        self.sin_ambas = 0  # notas que mencionan solo una de las palabras clave
        self.sin_fecha = 0  # notas con las palabras clave cuya fecha no se pudo comprobar
        self.revisadas = 0  # notas abiertas y leídas en la última búsqueda
        self._lock = threading.Lock()
        self._cache: Dict[str, dict] = {}
        self._sitios: Dict[str, dict] = {}
        self._descubiertos: List[dict] = []
        self.medios_usados: List[dict] = list(MEDIOS_CHACO)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    # ------------------------------------------------------------ utilidades
    def _contar(self, campo: str, n: int = 1):
        with self._lock:
            setattr(self, campo, getattr(self, campo) + n)

    @staticmethod
    def _corte() -> datetime:
        return _ahora() - timedelta(hours=HORAS_MAX)

    def _evaluar(self, medio: str, url: str, titulo: str, texto: str, pub: Optional[datetime],
                 fuente: str = "") -> Tuple[str, Optional[dict]]:
        """
        Decide si una nota sirve. Retorna (estado, noticia):
          'ign' no menciona ninguna palabra clave · 'amb' menciona solo una · 'nof' sin fecha comprobable ·
          'old' más antigua que HORAS_MAX · 'ok' vigente
        """
        palabras = [p for p, pat in _PATRONES.items() if pat.search(texto)]
        if not palabras:
            return "ign", None
        if COINCIDENCIA == "todas" and len(palabras) < len(PALABRAS_CLAVE):
            self._contar("sin_ambas")
            logger.info(f"✗ Descartada (solo menciona {', '.join(palabras)}): {titulo[:50]}...")
            return "amb", None

        if pub is None:  # la fecha tampoco está en la nota: se prueba con la dirección (/2026/09/28/)
            dt_url, exacta = _fecha_desde_url(url)
            if dt_url is not None and (exacta or dt_url < self._corte()):
                pub = dt_url
        if pub is None:
            # Sin fecha comprobable no se puede asegurar que esté dentro de las últimas 72 h: se descarta
            self._contar("sin_fecha")
            logger.info(f"✗ Descartada (sin fecha comprobable): {titulo[:50]}...")
            return "nof", None
        if pub < self._corte():
            self._contar("descartadas")
            logger.info(f"✗ Descartada (antigua, {pub:%d/%m %H:%M}): {titulo[:50]}...")
            return "old", None

        logger.info(f"✓ Encontrada: {titulo[:60]}...")
        return "ok", {
            "titulo": titulo[:150],  # Limitar a 150 caracteres
            "url": url,
            "medio": medio,
            "timestamp": _ahora().isoformat(),
            "palabra_clave": ", ".join(palabras),
            "palabras": palabras,
            "publicada": pub.isoformat(),
            "fuente": fuente,
        }

    # ------------------------------------------------------------ lectura de fechas y textos
    @staticmethod
    def _fecha_visible(soup, titulo: str) -> Optional[datetime]:
        """
        Para notas que no declaran la fecha en sus metadatos: la fecha escrita junto al título.
        Se toma el texto que rodea al <h1> de la nota (sin llegar a barras laterales ni a otras notas).
        """
        def palabras(t):
            return {w for w in re.findall(r'\w{4,}', t.lower())}

        ref = palabras(titulo)
        mejor, puntaje = None, 0.0
        for h1 in soup.find_all(["h1", "h2"]):
            p = palabras(h1.get_text(" "))
            if p and ref:
                sc = len(p & ref) / len(p | ref)
                if sc > puntaje:
                    mejor, puntaje = h1, sc
        if mejor is None:  # ningún <h1> se parece al título: se usa el último (el primero suele ser el logo)
            h1s = soup.find_all(["h1", "h2"])
            if not h1s:
                return None
            mejor = h1s[-1]

        nodo, zona = mejor, " ".join(mejor.get_text(" ").split())
        while nodo.parent is not None:
            nodo = nodo.parent
            t = " ".join(nodo.get_text(" ").split())
            if len(t) > 500:
                break
            zona = t
        return _fecha_en_texto(zona)

    @staticmethod
    def _fecha_de(soup) -> Optional[datetime]:
        # 1) metadatos de publicación (de más a menos confiable)
        for clave in ("article:published_time", "og:article:published_time", "datePublished",
                      "DC.date.issued", "publish_date", "pubdate", "date"):
            tag = (soup.find("meta", attrs={"property": clave}) or soup.find("meta", attrs={"name": clave})
                   or soup.find("meta", attrs={"itemprop": clave}))
            if tag and tag.get("content"):
                dt = _parsear_fecha(tag["content"])
                if dt:
                    return dt
        # 2) JSON-LD (datePublished)
        for s in soup.find_all("script", type="application/ld+json"):
            for valor in re.findall(r'"datePublished"\s*:\s*"([^"]+)"', s.string or s.get_text() or ""):
                dt = _parsear_fecha(valor)
                if dt:
                    return dt
        return None

    @staticmethod
    def _texto_de(soup, titulo: str) -> str:
        """
        Texto de la nota: título + resumen + cuerpo. Se evita el menú, la barra lateral y las
        notas relacionadas para no confundir menciones de otras notas con las de ésta.
        """
        partes = [titulo]
        for clave in ("og:title", "og:description", "description", "twitter:title", "twitter:description"):
            tag = soup.find("meta", attrs={"property": clave}) or soup.find("meta", attrs={"name": clave})
            if tag and tag.get("content"):
                partes.append(tag["content"])
        h1 = soup.find("h1")
        if h1:
            partes.append(h1.get_text(" "))

        cuerpo = soup.find(attrs={"itemprop": "articleBody"})
        if not cuerpo:
            cuerpo = soup.find(class_=re.compile(r'entry-content|post-content|article-body|article__body|'
                                                 r'nota-cuerpo|cuerpo|td-post-content|single-content|content-nota', re.I))
        if cuerpo and len(cuerpo.get_text(strip=True)) > 200:
            partes.append(cuerpo.get_text(" "))
        else:
            art = soup.find("article")
            ambito = art if art else soup
            partes.append(" ".join(p.get_text(" ") for p in ambito.find_all("p")))
        return " ".join(" ".join(partes).split())

    # ------------------------------------------------------------ memoria de cada sitio (WordPress / feed)
    def _cargar_sitios(self):
        try:
            s = json.loads(SITIOS_FILE.read_text(encoding="utf-8")) if SITIOS_FILE.exists() else {}
        except Exception:
            s = {}
        limite = _ahora() - timedelta(days=SITIOS_DIAS)
        self._sitios = {k: v for k, v in s.items() if not _es_anterior(v.get("t"), limite)}

    def _guardar_sitios(self):
        try:
            SITIOS_FILE.write_text(json.dumps(self._sitios, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error(f"No se pudo guardar la memoria de sitios: {str(e)}")

    @staticmethod
    def _origen(medio: Dict) -> str:
        return re.match(r"(https?://[^/]+)", medio['url']).group(1)

    def _sitio(self, medio: Dict) -> dict:
        with self._lock:
            return self._sitios.setdefault(self._origen(medio), {"t": _ahora().isoformat()})

    # ------------------------------------------------------------ medios descubiertos
    def _cargar_descubiertos(self):
        try:
            self._descubiertos = json.loads(DESCUBIERTOS_FILE.read_text(encoding="utf-8")) if DESCUBIERTOS_FILE.exists() else []
        except Exception:
            self._descubiertos = []

    def _medios_todos(self) -> List[dict]:
        """Medios de la lista + medios que Google Noticias fue mostrando en búsquedas anteriores."""
        extra = [{"nombre": d["nombre"], "url": d["url"], "zona": "Descubierto por Google", "ligero": True}
                 for d in self._descubiertos]
        return list(MEDIOS_CHACO) + extra

    def total_medios(self) -> int:
        self._cargar_descubiertos()
        return len(self._medios_todos())

    def _registrar_descubiertos(self, notas_google: List[dict]):
        """Los medios nuevos que aparecen en Google Noticias se agregan para consultarlos directamente la próxima vez."""
        conocidos = {urlparse(m['url']).netloc.replace("www.", "") for m in self._medios_todos()}
        nuevos = []
        for n in notas_google:
            host = n.get("sitio", "")
            if host and host not in conocidos and len(self._descubiertos) + len(nuevos) < MAX_DESCUBIERTOS:
                conocidos.add(host)
                nuevos.append({"nombre": n["medio"], "url": f"https://{host}", "visto": _ahora().isoformat()})
                logger.info(f"➕ Medio nuevo descubierto: {n['medio']} ({host})")
        if nuevos:
            self._descubiertos += nuevos
            try:
                DESCUBIERTOS_FILE.write_text(json.dumps(self._descubiertos, ensure_ascii=False, indent=1), encoding="utf-8")
            except Exception as e:
                logger.error(f"No se pudo guardar medios descubiertos: {str(e)}")

    # ------------------------------------------------------------ caché de notas ya abiertas
    def _desde_cache(self, url: str) -> Tuple[bool, Optional[dict]]:
        """(estaba_en_caché, noticia_vigente). Si estaba, también suma el motivo de descarte a los contadores."""
        c = self._cache.get(url)
        if c is None:
            return False, None
        if c["r"] == "ok" and c.get("n"):  # vigente la vez anterior: se vuelve a comprobar la ventana
            if _a_dt(c["n"]["publicada"]) >= self._corte():
                return True, c["n"]
            self._contar("descartadas")
        elif c["r"] == "amb":
            self._contar("sin_ambas")
        elif c["r"] == "nof":
            self._contar("sin_fecha")
        elif c["r"] == "old":
            self._contar("descartadas")
        return True, None

    # ------------------------------------------------------------ fuente 1: WordPress
    def _buscar_wp(self, medio: Dict) -> Optional[List[dict]]:
        """
        Busca en el buscador interno del sitio (API REST de WordPress).
        Retorna las notas vigentes, o None si el sitio no es WordPress / no permite la consulta.
        """
        sitio = self._sitio(medio)
        if sitio.get("wp") is False:
            return None
        origen = self._origen(medio)
        buscar = (TERMINOS[PALABRAS_CLAVE[0]] if COINCIDENCIA == "todas"
                  else [t for p in PALABRAS_CLAVE for t in TERMINOS[p]])
        desde = (datetime.now(timezone.utc) - timedelta(hours=HORAS_MAX + 36)).strftime("%Y-%m-%dT%H:%M:%S")
        posts, vistos = [], set()
        for palabra in buscar:
            try:
                r = requests.get(f"{origen}/wp-json/wp/v2/posts", headers=self.headers, timeout=12,
                                 params={"search": palabra, "after": desde, "per_page": 50,
                                         "_fields": "date_gmt,link,title,content,excerpt"})
            except requests.exceptions.RequestException:
                return None
            if r.status_code >= 500:
                return None  # falla momentánea: no se recuerda
            if r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
                sitio["wp"] = False  # no es WordPress (o no deja consultar): no se vuelve a intentar por unos días
                return None
            try:
                datos = r.json()
            except ValueError:
                sitio["wp"] = False
                return None
            if not isinstance(datos, list):
                sitio["wp"] = False
                return None
            sitio["wp"] = True
            for p in datos:
                if p.get("link") and p["link"] not in vistos:
                    vistos.add(p["link"])
                    posts.append(p)

        noticias = []
        for p in posts:
            try:
                titulo = " ".join(BeautifulSoup(p["title"]["rendered"], "html.parser").get_text(" ").split())
                cuerpo = BeautifulSoup(p["content"]["rendered"] + " " + p["excerpt"]["rendered"], "html.parser").get_text(" ")
                pub = datetime.fromisoformat(p["date_gmt"]).replace(tzinfo=timezone.utc).astimezone(_TZ)
            except (KeyError, ValueError, TypeError):
                continue
            self._contar("revisadas")
            estado, n = self._evaluar(medio['nombre'], p["link"], titulo, f"{titulo} {cuerpo}", pub, "wp")
            if n:
                noticias.append(n)
        return noticias

    # ------------------------------------------------------------ fuente 2: feeds RSS / Atom
    def _items_feed(self, url: str) -> Optional[List[dict]]:
        """Lee un feed RSS/Atom. None si la dirección no es un feed. Las fallas de red se propagan."""
        r = requests.get(url, headers=self.headers, timeout=10)
        if r.status_code != 200:
            return None
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            return None
        ns_c = "{http://purl.org/rss/1.0/modules/content/}encoded"
        ns_a = "{http://www.w3.org/2005/Atom}"
        items = []
        for it in root.iter("item"):
            d = it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")
            try:
                pub = parsedate_to_datetime(d).astimezone(_TZ) if d and "," in d else _parsear_fecha(d)
            except (TypeError, ValueError):
                pub = None
            items.append({"titulo": " ".join((it.findtext("title") or "").split()), "url": (it.findtext("link") or "").strip(),
                          "pub": pub, "html": (it.findtext(ns_c) or "") + " " + (it.findtext("description") or "")})
        for it in root.iter(ns_a + "entry"):
            link = it.find(ns_a + "link")
            d = it.findtext(ns_a + "published") or it.findtext(ns_a + "updated")
            items.append({"titulo": " ".join((it.findtext(ns_a + "title") or "").split()),
                          "url": (link.get("href") if link is not None else "").strip(), "pub": _parsear_fecha(d),
                          "html": (it.findtext(ns_a + "content") or "") + " " + (it.findtext(ns_a + "summary") or "")})
        return [i for i in items if i["url"]] or None

    def _leer_feed(self, medio: Dict, soup=None) -> Optional[List[dict]]:
        """Busca (y recuerda) el feed del sitio. None si no tiene."""
        sitio = self._sitio(medio)
        if sitio.get("feed") == "":
            return None
        origen = self._origen(medio)
        candidatos = [sitio["feed"]] if sitio.get("feed") else []
        if not candidatos:
            if soup is not None:
                for l in soup.find_all("link", attrs={"rel": "alternate"}):
                    if "xml" in (l.get("type") or "") and l.get("href"):
                        candidatos.append(urljoin(medio['url'], l["href"]))
            candidatos += [origen + p for p in FEEDS_COMUNES]
        hubo_error = False
        for c in dict.fromkeys(candidatos):
            try:
                items = self._items_feed(c)
            except requests.exceptions.RequestException:
                hubo_error = True
                continue
            if items:
                sitio["feed"] = c
                return items
        if not hubo_error:
            sitio["feed"] = ""  # sin feed: no se vuelve a buscar por unos días
        return None

    def _procesar_feed(self, medio: Dict, items: List[dict], vistos: set) -> List[dict]:
        """Las notas del feed traen su fecha exacta (y a veces el texto completo)."""
        noticias, pendientes = [], []
        margen = self._corte() - timedelta(hours=6)
        for it in items:
            if it["pub"] is not None and it["pub"] < margen:
                continue  # ya es vieja: ni se abre
            if it["url"] in vistos:
                continue
            vistos.add(it["url"])
            en_cache, n = self._desde_cache(it["url"])
            if en_cache:
                if n:
                    noticias.append(n)
                continue
            texto = f"{it['titulo']} {BeautifulSoup(it['html'], 'html.parser').get_text(' ')}"
            if len(texto) > 700:  # el feed trae la nota completa: no hace falta abrirla
                self._contar("revisadas")
                estado, n = self._evaluar(medio['nombre'], it["url"], it["titulo"], texto, it["pub"])
                with self._lock:
                    self._cache[it["url"]] = {"t": _ahora().isoformat(), "r": estado, "n": n}
                if n:
                    noticias.append(n)
            else:
                pendientes.append(it)
        with ThreadPoolExecutor(max_workers=4) as pool:
            for res in pool.map(lambda i: self._abrir_nota(medio['nombre'], i["url"], i["titulo"], i["pub"]),
                                pendientes[:MAX_NOTAS_NUEVAS_POR_MEDIO]):
                if res and res[1]:
                    noticias.append(res[1])
        return noticias

    # ------------------------------------------------------------ fuente 3: notas de la portada
    def _enlaces_de_notas(self, soup, base: str, patron: Optional[str] = None) -> List[Tuple[str, str, bool]]:
        """Enlaces de la portada que parecen notas del propio medio: [(url, texto, menciona_palabra)]"""
        host = urlparse(base).netloc.replace("www.", "")
        salida, vistos = [], set()
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:', 'whatsapp:')):
                continue
            u = urljoin(base, href).split('#')[0]
            p = urlparse(u)
            if p.scheme not in ('http', 'https') or host not in p.netloc.replace("www.", ""):
                continue
            if re.search(r'\.(jpe?g|png|gif|webp|svg|pdf|mp3|mp4|css|js|xml)(\?|$)', p.path, re.I):
                continue
            if re.search(r'/(category|categoria|categorias|tag|tags|etiqueta|author|autor|page|pagina|seccion|secciones|'
                         r'feed|wp-content|wp-admin|wp-json|search|buscar|contacto|publicidad|tema|temas)(/|$)', p.path, re.I):
                continue
            texto = ' '.join(a.get_text().split())
            tiene_palabra = any(pat.search(texto) for pat in _PATRONES.values())
            # un enlace que es solo la palabra ("INSSSEP") es un menú/etiqueta, no una nota
            if texto.lower() in (k.lower() for k in PALABRAS_CLAVE):
                continue
            if patron:  # el medio indica qué direcciones son notas
                if not re.search(patron, u) or u in vistos:
                    continue
            else:
                slug = p.path.rstrip('/').split('/')[-1]
                parece_nota = (len(slug) > 20 and '-' in slug) or (p.query and len(texto) > 25) or re.search(r'/\d{5,}', p.path)
                if not (parece_nota or tiene_palabra) or u in vistos:
                    continue
            vistos.add(u)
            salida.append((u, texto, tiene_palabra))
        return salida

    @staticmethod
    def _fecha_de_enlace(texto: str) -> Optional[datetime]:
        """Algunos listados escriben la fecha al comienzo del enlace ("29 SEP ...", "01/10/26 ...")."""
        limpio = re.sub(r'^[^\w]+', '', texto)
        if _RE_DIA_MES.match(limpio) or _RE_NUM.match(limpio):
            return _fecha_en_texto(limpio[:40])
        return None

    def _abrir_nota(self, medio: str, url: str, texto_enlace: str, pub_fija: Optional[datetime] = None) -> Optional[Tuple[str, Optional[dict]]]:
        """Abre una nota, la evalúa y la guarda en caché. None si no se pudo abrir (se reintenta en la próxima búsqueda)."""
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.content, 'html.parser')
        except requests.exceptions.RequestException:
            return None
        self._contar("revisadas")
        meta = soup.find("meta", attrs={"property": "og:title"})
        h1 = soup.find("h1") or soup.find("h2")
        titulo = " ".join(((meta.get("content") if meta and meta.get("content") else None)
                           or (h1.get_text(" ") if h1 else None) or texto_enlace or url).split())
        pub = (pub_fija or self._fecha_de(soup) or self._fecha_visible(soup, titulo)
               or self._fecha_de_enlace(texto_enlace))
        estado, noticia = self._evaluar(medio, url, titulo, self._texto_de(soup, titulo), pub)
        with self._lock:
            self._cache[url] = {"t": _ahora().isoformat(), "r": estado, "n": noticia}
        return estado, noticia

    def _escanear_portada(self, medio: Dict, soup_portada, vistos: set) -> List[dict]:
        """Abre las notas de la portada (y de las páginas extra del medio) que todavía no se habían revisado."""
        base = medio['url']
        enlaces = self._enlaces_de_notas(soup_portada, base, medio.get("patron"))
        paginas = [f"{base}{'&' if '?' in base else '?'}page={i}" for i in range(2, int(medio.get("paginas", 1)) + 1)]
        paginas += [urljoin(base, e) for e in medio.get("extra_urls", [])]
        for p in paginas:
            try:
                r = requests.get(p, headers=self.headers, timeout=10)
                if r.status_code == 200:
                    enlaces += self._enlaces_de_notas(BeautifulSoup(r.content, 'html.parser'), p, medio.get("patron"))
            except requests.exceptions.RequestException:
                pass

        noticias, pendientes, ya = [], [], set()
        for url, texto, tiene_palabra in enlaces:
            if url in vistos or url in ya:
                continue
            ya.add(url)
            en_cache, n = self._desde_cache(url)
            if en_cache:
                if n:
                    noticias.append(n)
            else:
                pendientes.append((not tiene_palabra, url, texto))  # primero las que ya mencionan una palabra
        vistos |= ya

        pendientes.sort(key=lambda x: x[0])
        with ThreadPoolExecutor(max_workers=4) as pool:
            for res in pool.map(lambda x: self._abrir_nota(medio['nombre'], x[1], x[2]), pendientes[:MAX_NOTAS_NUEVAS_POR_MEDIO]):
                if res and res[1]:
                    noticias.append(res[1])
        return noticias

    # ------------------------------------------------------------ fuente 4: Google Noticias
    def _google_noticias(self) -> List[dict]:
        """Notas recientes de cualquier medio indexado por Google Noticias (RSS público)."""
        dias = max(1, -(-HORAS_MAX // 24))
        if COINCIDENCIA == "todas":
            consultas = [(" ".join(f'"{p}"' for p in PALABRAS_CLAVE), None)]
        else:  # una consulta por cada nombre (y sinónimo); los que no son "INSSSEP" se acotan a Chaco para evitar homónimos
            consultas = [(f'"{t}"' if p.lower() == "insssep" else f'"{t}" Chaco', p)
                         for p in PALABRAS_CLAVE for t in TERMINOS[p]]
        noticias, vistos = [], set()
        for q, kw in consultas:
            try:
                r = requests.get("https://news.google.com/rss/search", headers=self.headers, timeout=15,
                                 params={"q": f"{q} when:{dias}d", "hl": "es-419", "gl": "AR", "ceid": "AR:es-419"})
                items = ET.fromstring(r.content).findall(".//item")
            except (requests.exceptions.RequestException, ET.ParseError) as e:
                logger.warning(f"Google Noticias no respondió: {str(e)[:80]}")
                continue
            for it in items:
                try:
                    pub = parsedate_to_datetime(it.findtext("pubDate")).astimezone(_TZ)
                except (TypeError, ValueError):
                    continue
                medio = (it.findtext("source") or "Google Noticias").strip()
                titulo = " ".join((it.findtext("title") or "").split())
                if titulo.endswith(" - " + medio):
                    titulo = titulo[: -len(medio) - 3]
                link = it.findtext("link") or ""
                if not link or not titulo or link in vistos or pub < self._corte():
                    continue
                vistos.add(link)
                src = it.find("source")
                sitio = urlparse(src.get("url", "")).netloc.replace("www.", "") if src is not None else ""
                palabras = list(PALABRAS_CLAVE) if COINCIDENCIA == "todas" else [kw]
                noticias.append({
                    "titulo": titulo[:150], "url": link, "medio": medio,
                    "timestamp": _ahora().isoformat(), "palabra_clave": ", ".join(palabras),
                    "palabras": palabras, "publicada": pub.isoformat(), "fuente": "google", "sitio": sitio,
                })
                logger.info(f"✓ Google Noticias: {titulo[:60]}... ({medio})")
        return noticias

    # ------------------------------------------------------------ orquestación
    def scrapear_medio(self, medio: Dict) -> List[Dict]:
        """
        Busca en un medio: 1) su buscador interno (WordPress); si no tiene, 2) su feed RSS y 3) las notas de su portada.
        Los medios "ligeros" (descubiertos por Google) solo se consultan por WordPress o feed.
        """
        try:
            logger.info(f"Buscando en {medio['nombre']}...")
            wp = self._buscar_wp(medio)
            if wp is not None:
                return wp

            soup = None
            if not medio.get("ligero"):
                response = requests.get(medio['url'], headers=self.headers, timeout=10)
                response.encoding = 'utf-8'
                if response.status_code != 200:
                    logger.warning(f"Error al acceder a {medio['nombre']}: {response.status_code}")
                    self.fallidos[medio['nombre']] = (
                        "Bloquea al scraper (error 403)" if response.status_code == 403
                        else f"El sitio devolvió error {response.status_code}")
                    return []
                soup = BeautifulSoup(response.content, 'html.parser')

            noticias, vistos = [], set()
            try:
                items = self._leer_feed(medio, soup)
            except Exception as e:
                logger.warning(f"Feed de {medio['nombre']}: {str(e)[:80]}")
                items = None
            if items:
                noticias += self._procesar_feed(medio, items, vistos)
            if soup is not None:
                noticias += self._escanear_portada(medio, soup, vistos)
            return noticias
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al scrapear {medio['nombre']}: {str(e)[:120]}")
            if not medio.get("ligero"):
                self.fallidos[medio['nombre']] = self._motivo(e)
        except Exception as e:
            logger.error(f"Error inesperado en {medio['nombre']}: {str(e)}")
            if not medio.get("ligero"):
                self.fallidos[medio['nombre']] = "Error inesperado al leer el sitio"
        return []

    @staticmethod
    def _motivo(e: Exception) -> str:
        """Traduce un error de conexión a un motivo legible"""
        s = str(e)
        if 'getaddrinfo' in s or 'NameResolution' in s:
            return "El dominio no existe (revisar la dirección)"
        if 'SSL' in s or 'certificate' in s:
            return "Certificado de seguridad inválido"
        if 'imed out' in s or 'Timeout' in type(e).__name__:
            return "No respondió a tiempo"
        return "No se pudo conectar"

    @staticmethod
    def _reglas() -> str:
        return f"{COINCIDENCIA}|{','.join(PALABRAS_CLAVE)}|{HORAS_MAX}"

    def _cargar_cache(self):
        try:
            c = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}
        except Exception:
            c = {}
        # lo revisado vale solo para las mismas reglas (palabras, coincidencia y horas): si cambiaron, se empieza de cero
        if c.get("__reglas__") != self._reglas():
            c = {}
        limite = _ahora() - timedelta(days=CACHE_DIAS)
        self._cache = {u: v for u, v in c.items() if u != "__reglas__" and not _es_anterior(v.get("t"), limite)}

    def _guardar_cache(self):
        try:
            CACHE_FILE.write_text(json.dumps({"__reglas__": self._reglas(), **self._cache}, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error(f"No se pudo guardar la caché: {str(e)}")

    def scrapear_todos(self, on_progress=None):
        """
        Busca en todos los medios en paralelo (MAX_HILOS a la vez) y en Google Noticias.
        on_progress(medio, cantidad): se llama al terminar cada medio (opcional).
        Retorna (lista_de_noticias_vigentes, {medio: cantidad})
        """
        self.fallidos = {}
        self.descartadas = self.sin_ambas = self.sin_fecha = self.revisadas = 0
        self._cargar_cache()
        self._cargar_sitios()
        self._cargar_descubiertos()
        self.medios_usados = self._medios_todos()

        def tarea(medio):
            noticias = self.scrapear_medio(medio)
            if on_progress:
                on_progress(medio, len(noticias))
            return noticias

        with ThreadPoolExecutor(max_workers=MAX_HILOS) as pool:
            listas = list(pool.map(tarea, self.medios_usados))
        self._guardar_cache()
        self._guardar_sitios()

        conteo = {m['nombre']: len(n) for m, n in zip(self.medios_usados, listas)}
        todas, vistas, claves = [], set(), set()
        for lista in listas:
            for n in lista:
                if n['url'] not in vistas:
                    vistas.add(n['url'])
                    claves.add((_norm(n['titulo']), urlparse(n['url']).netloc.replace("www.", "")))
                    todas.append(n)

        # Google Noticias: solo lo que no se encontró ya en los propios sitios (mismo título y mismo sitio).
        # Una misma gacetilla publicada por otro medio sí se muestra.
        google = self._google_noticias()
        self._registrar_descubiertos(google)  # medios nuevos: la próxima vez se consultan directamente
        for n in google:
            clave = (_norm(n['titulo']), n.pop("sitio", ""))
            if clave not in claves:
                claves.add(clave)
                todas.append(n)

        # Más recientes primero (las fechas pueden venir con distinta zona horaria: se comparan como fechas)
        todas.sort(key=lambda n: _a_dt(n['publicada']), reverse=True)
        return todas, conteo

    def ejecutar_busqueda_completa(self, on_progress=None) -> Dict:
        """
        Ejecuta búsqueda en todos los medios
        Retorna resultado consolidado
        """
        logger.info("=" * 60)
        logger.info(f"INICIANDO BÚSQUEDA - {_ahora().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        inicio = time.time()
        todas_noticias, conteo = self.scrapear_todos(on_progress)
        nuevas = self.marcar_nuevas(todas_noticias)

        resultado = {
            "timestamp": _ahora().isoformat(),
            "palabra_clave": PALABRA_CLAVE,
            "palabras_clave": PALABRAS_CLAVE,
            "horas_maximas": HORAS_MAX,
            "total_noticias": len(todas_noticias),
            "noticias_nuevas": len(nuevas),
            "descartadas_antiguas": self.descartadas,
            "descartadas_sin_palabras": self.sin_ambas,
            "descartadas_sin_fecha": self.sin_fecha,
            "notas_revisadas": self.revisadas,
            "coincidencia": COINCIDENCIA,
            "medios_buscados": len(self.medios_usados),
            "medios_fallidos": sorted(self.fallidos),
            "duracion_seg": round(time.time() - inicio, 1),
            "medios_detalle": [
                {
                    "nombre": m['nombre'],
                    "zona": m.get('zona', ''),
                    "url": m['url'],
                    "ok": m['nombre'] not in self.fallidos,
                    "motivo": self.fallidos.get(m['nombre'], ''),
                    "noticias": conteo.get(m['nombre'], 0),
                }
                for m in self.medios_usados
            ],
            "noticias": todas_noticias
        }

        # Guardar resultado localmente
        self._guardar_resultado(resultado)

        for n in nuevas:
            logger.info(f"🆕 NUEVA [{n['medio']}] {n['titulo'][:100]} -> {n['url']}")
        logger.info(f"✓ Búsqueda completada. Noticias: {len(todas_noticias)} ({len(nuevas)} nuevas, "
                    f"{self.descartadas} descartadas por antiguas)")
        logger.info("=" * 60)

        return resultado

    # ------------------------------------------------------------ historial
    def _leer_historial(self) -> dict:
        try:
            return json.loads(HISTORIAL_FILE.read_text(encoding='utf-8')) if HISTORIAL_FILE.exists() else {}
        except Exception as e:
            logger.error(f"Historial ilegible, se reinicia: {str(e)}")
            return {}

    def marcar_nuevas(self, noticias: List[Dict]) -> List[Dict]:
        """
        Marca cada noticia con "nueva": True/False según si su URL ya estaba
        en el historial, y registra las nuevas. Retorna solo las nuevas.
        """
        historial = self._leer_historial()

        nuevas = []
        for n in noticias:
            n['nueva'] = n['url'] not in historial
            if n['nueva']:
                historial[n['url']] = {"titulo": n['titulo'], "medio": n['medio'],
                                       "visto": n['timestamp'], "publicada": n.get('publicada')}
                nuevas.append(n)

        # olvidar lo muy viejo para que el archivo no crezca para siempre
        limite = _ahora() - timedelta(days=HISTORIAL_DIAS)
        for url in [u for u, d in historial.items() if _es_anterior(d.get('visto'), limite)]:
            del historial[url]

        try:
            HISTORIAL_FILE.write_text(json.dumps(historial, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"No se pudo guardar el historial: {str(e)}")
        return nuevas

    def _guardar_resultado(self, resultado: Dict):
        """Guarda el último resultado en JSON"""
        try:
            with open(RESULTADOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            logger.info(f"Resultado guardado en {RESULTADOS_FILE}")
        except Exception as e:
            logger.error(f"Error al guardar resultado: {str(e)}")

    def obtener_ultimas_noticias(self) -> Dict:
        """Lee el último resultado guardado"""
        try:
            if RESULTADOS_FILE.exists():
                with open(RESULTADOS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error al leer noticias: {str(e)}")

        return {"noticias": [], "total_noticias": 0}


def _es_anterior(iso: Optional[str], limite: datetime) -> bool:
    try:
        return bool(iso) and _a_dt(iso) < limite
    except ValueError:
        return False


class SchedulerInsssep:
    """Maneja la ejecución automática cada 3 horas"""

    def __init__(self):
        self.scraper = InsssepScraper()
        self.scheduler = BackgroundScheduler()

    def tarea_programada(self):
        """Tarea que ejecuta el scheduler"""
        try:
            self.scraper.ejecutar_busqueda_completa()
        except Exception as e:
            logger.error(f"Error en tarea programada: {str(e)}")

    def iniciar(self, ejecutar_ahora: bool = True):
        """
        Inicia el scheduler
        ejecutar_ahora: si True, ejecuta la búsqueda inmediatamente
        """
        if ejecutar_ahora:
            logger.info("Ejecutando búsqueda inicial...")
            self.tarea_programada()

        # Programar para cada 3 horas
        self.scheduler.add_job(
            self.tarea_programada,
            'interval',
            hours=3,
            id='insssep_scraper'
        )

        self.scheduler.start()
        logger.info("✓ Scheduler iniciado. Búsquedas cada 3 horas.")

        # Mantener el programa corriendo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler detenido por el usuario")
            self.scheduler.shutdown()


if __name__ == "__main__":
    scheduler = SchedulerInsssep()
    scheduler.iniciar(ejecutar_ahora=True)
