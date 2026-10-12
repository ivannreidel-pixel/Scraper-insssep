# 📰 BUSCADOR DE NOTICIAS — INSSSEP

Busca en ~100 medios de Chaco, el portal del Gobierno y el sitio oficial del INSSSEP las noticias que mencionan **INSSSEP o Rafael Meneses** (basta con una de las dos), conserva solo las de las
**últimas 72 horas** y las muestra en un panel web simple.

- ✅ Se inicia **a mano** con un acceso directo del Escritorio (no arranca solo con Windows)
- ✅ Panel visual accesible desde **cualquier PC o teléfono**
- ✅ Botón **Buscar ahora** + modo **automático** opcional (cada 3 horas, configurable)
- ✅ Descarta toda noticia de **más de 72 h** y marca las **nuevas**
- ✅ Botón **Generar link** para compartir el panel con alguien en otra red
- ✅ Sin contraseñas ni PIN

---

## 🚀 Instalación (una sola vez)

1. Instalar Python 3.11+ desde https://www.python.org/downloads/ (tildar **"Add Python to PATH"**).
2. En esta carpeta, doble clic en **`INSTALAR.bat`** (instala las librerías y crea el acceso directo).

   Manual: `pip install requests beautifulsoup4 apscheduler fastapi uvicorn` y luego en PowerShell `.\crear_acceso_directo.ps1`.

---

## ▶️ Uso diario

### 1. Abrir el panel
Doble clic en **"INSSSEP Scraper"** del Escritorio (o `INSSSEP.bat`, o `python api_noticias.py`).

Se abre una ventana negra y el navegador. La ventana muestra:

```
En esta PC:           http://localhost:8000
Desde otro equipo:    http://192.168.1.25:8000   (misma red Wi-Fi)
```

> **Para apagar el sistema: cerrá la ventana negra.** Mientras esté abierta, el panel funciona.

### 2. Qué se puede hacer en el panel
| Botón | Qué hace |
|---|---|
| **Buscar ahora** | Busca en todos los medios en el momento (1-2 minutos, con barra de avance) |
| **Búsqueda automática** | Si la activás, busca sola cada 1/2/3/6/12/24 h mientras el programa siga abierto |
| **Todas las palabras / Solo nuevas** | Filtra por INSSSEP o por Rafael Meneses, o por noticias que no habían aparecido antes |
| **Historial** | Noticias encontradas en los últimos 30 días |
| **Generar link** | Crea una dirección para compartir el panel (ver abajo) |

---

## 🌍 Compartir el panel con otra persona (otra casa, otra red, datos móviles)

1. Abrir el panel en **tu PC** (acceso directo "INSSSEP Scraper").
2. Arriba de los botones, en la tarjeta **"Compartir con otra persona"**, tocar **Generar link**.
3. En unos segundos aparece una dirección tipo `https://algo-algo-algo.trycloudflare.com`. Tocar **Copiar link**
   y enviarla por WhatsApp. La otra persona la abre en su navegador y ya está.
4. Para cortar el acceso: **Dejar de compartir** (o cerrar la ventana negra).

Requisito (una sola vez en cada PC): instalar `cloudflared`, gratis y sin cuenta. En PowerShell:
```powershell
winget install --id Cloudflare.cloudflared
```
y volver a abrir el programa.

Lo que hay que saber:
- El link **cambia cada vez** que lo generás. Hay que mandar el nuevo.
- Funciona **solo mientras tu PC esté encendida y la ventana negra abierta**.
- **No hay PIN**: cualquiera que tenga el link puede ver el panel y usar «Buscar ahora» y «Automático». Compartilo solo con quien quieras.
- Generar o cortar el link **solo se puede hacer desde tu PC**, nunca desde el link público.
- Para que sea permanente y no dependa de tu PC, habría que alojar el sistema en un servidor en la nube.

---

## ☁️ Publicar en internet de forma permanente (hosting gratuito)

El panel de tu PC solo funciona mientras la PC está encendida. Para que **cualquier persona lo abra en cualquier dispositivo,
las 24 horas, sin depender de tu PC**, se publica gratis en **GitHub** (no hace falta tarjeta ni pagar nada):

- **GitHub Pages** aloja la página (siempre disponible, con dirección `https://TU-USUARIO.github.io/buscador-noticias/`).
- **GitHub Actions** busca las noticias **cada 3 horas** y actualiza la página sola.

### Cómo publicarlo
Doble clic en **`PUBLICAR_EN_GITHUB.bat`** y seguir los pasos de la ventana:
1. Instala Git y GitHub CLI si faltan (pide confirmación).
2. Abre el navegador para que **inicies sesión en GitHub** (si no tenés cuenta, se crea gratis ahí mismo).
3. Sube estos archivos a un repositorio **público** de tu cuenta y activa GitHub Pages.
4. Lanza la primera actualización (5 a 8 minutos) y, al terminar, **abre y copia la dirección** para que la compartas.

Es repetible: si más adelante cambiás algo (`config.json`, `medios.py`...), volvé a ejecutarlo y se actualiza.

### Cómo funciona la versión publicada
- Es una página de **solo lectura**: muestra las notas de las últimas 72 horas, la hora de la última actualización y cuándo
  se espera la próxima. No tiene botones «Buscar ahora» ni «Automático» (esos son del panel de tu PC).
- En la versión publicada, **«Nueva» = detectada en las últimas 24 horas**.
- Para forzar una actualización: en GitHub → pestaña **Actions** → «Buscar noticias y publicar» → **Run workflow**
  (también está el enlace «Actualizar ahora» en la propia página, visible para todos pero solo funciona para quien administra).
- Para cambiar la frecuencia: editar `.github/workflows/buscar.yml` (línea `cron`) y, en `config.json`, lo que haga falta.
- Las palabras clave, las 72 horas y la lista de medios se cambian igual que en el panel de la PC (`config.json`, `medios.py`),
  editando los archivos en GitHub (lápiz ✏️ del archivo) o con el script.

### Qué hay que saber
- **Es público:** cualquiera que tenga la dirección puede abrirla (la página pide a los buscadores que no la indexen, pero no es privada).
  Lo publicado son enlaces a notas de medios y el logo del INSSSEP.
- **Costo: $0.** Los repositorios públicos tienen GitHub Actions y Pages gratis (sin límite práctico para este uso).
- **Los datos se actualizan cada ~3 horas**, no al instante. El horario de GitHub puede demorarse unos minutos.
- La búsqueda corre en servidores de GitHub (en el exterior): **algún medio podría bloquear esas conexiones**.
  La página muestra «Medios consultados»: si ese número es mucho menor que en tu PC, avisá.
- GitHub pausa los calendarios sin actividad de 60 días; el flujo se vuelve a habilitar solo en cada ejecución, y si algún día
  se pausara, se reactiva con un clic en la pestaña Actions.

---

## 🔍 Cómo busca

Para no perder notas, el sistema combina **cuatro vías** (por cada medio usa la mejor disponible):

1. **Buscador interno del sitio (WordPress).** Unos 48 medios usan WordPress; a esos se les pregunta directamente
   «¿qué notas de los últimos días mencionan INSSSEP?». Encuentra notas **aunque ya no estén en la portada** y aunque
   la palabra **no esté en el título**, con fecha y texto exactos.
2. **Feed RSS del sitio.** Unos 13 medios más publican un feed con sus últimas notas, con **fecha exacta de publicación**
   (y a veces el texto completo).
3. **Notas de la portada.** Se leen las notas que muestra la portada y se **abre cada una** para revisar su texto.
   Lo ya revisado se recuerda (`notas_revisadas.json`): la primera búsqueda tarda 2-3 minutos y las siguientes menos de 1.
4. **Google Noticias.** Suma notas de medios que no están en la lista. **Los medios nuevos que aparecen se agregan solos**
   (`medios_descubiertos.json`) y desde la búsqueda siguiente se consultan directamente.

Además hay dos **fuentes oficiales** configuradas: el portal de noticias del Gobierno del Chaco (`chaco.gob.ar/noticias`,
8 páginas de listado) y el sitio del propio INSSSEP (sección Publicaciones).

Cada nota se acepta solo si cumple **las dos condiciones** (palabras clave y últimas 72 horas):

### 🔤 Palabras clave
La nota debe **mencionar INSSSEP o Rafael Meneses** (basta una de las dos; del nombre se exige la frase completa, «Meneses» solo no cuenta) en su texto: título, resumen o cuerpo, sin contar
menú, barra lateral ni notas relacionadas. Un mismo apellido puede pertenecer a otra persona: revisá el título.
### ⏱️ Últimas 72 horas
La fecha de publicación se busca en este orden: datos ocultos de la nota → dirección (`/2026/09/28/`) → fecha escrita
junto al título («24 septiembre, 2026», «hace 3 horas»...).
- Más de 72 h → **se descarta**.
- Si **no se puede comprobar la fecha** → **también se descarta** (no se puede asegurar que sea reciente). Algunos
  medios no muestran la fecha de sus notas; las suyas no aparecerán.
- Si una fecha trae solo el día, se toma el mediodía.

Se configura en `config.json` (hay que reiniciar el programa):
- `"palabras_clave": ["INSSSEP", "Rafael Meneses"]`
- `"coincidencia": "cualquiera"` (poné `"todas"` para exigir que la nota mencione las dos palabras a la vez)
- `"horas_maximas": 72`

Las palabras se buscan completas y sin distinguir mayúsculas.

---

## 🔎 Búsqueda por consola (opcional)

```bash
python scraper_manual.py                          # busca ya y muestra el resultado en consola
python scraper_manual.py http://servidor-remoto   # además lo envía a un servidor
```

Guarda en `ultimas_noticias.json` y marca las nuevas con 🆕.

---

## ⚙️ Configuración

- **Intervalo del modo automático:** se cambia desde el panel (se guarda en `config.json`).
- **Puerto:** `config.json` → `"puerto"` (por defecto 8000), o `python api_noticias.py --port 8001`.
- **Agregar o quitar medios:** editar `medios.py`, formato `("Nombre", "https://sitio.com", "Zona")`.
- Los medios que solo existen en Facebook/Instagram no se consultan (requieren login).

---

## 🔌 API (para integrar con otras herramientas)

| Endpoint | Descripción |
|---|---|
| `GET /api/estado` | Estado actual (buscando, automático, última búsqueda, link público) |
| `GET /api/noticias` | Última búsqueda completa |
| `GET /api/historial?limite=200` | Historial de noticias |
| `POST /api/buscar` | Lanza una búsqueda |
| `POST /api/automatico` | `{"activo": true, "horas": 3}` |
| `POST /api/compartir` | `{"activo": true}` genera / `false` corta el link público (solo desde la PC) |
| `GET /health` | Health check |

---

## 🐛 Problemas frecuentes

| Problema | Solución |
|---|---|
| "No module named ..." | `pip install requests beautifulsoup4 apscheduler fastapi uvicorn` |
| El teléfono no abre la dirección de la Wi-Fi | Misma red Wi-Fi; permitir Python en el Firewall (Redes privadas). O usar «Generar link» |
| «Generar link» dice que falta cloudflared | `winget install --id Cloudflare.cloudflared` y reabrir el programa |
| "El panel ya está abierto" | Ya hay una ventana corriendo; se abre el navegador sobre esa |
| Cambié `config.json` y no pasa nada | Cerrar la ventana negra y volver a abrir el programa |
| Puerto 8000 ocupado | `python api_noticias.py --port 8001` |
| Un medio aparece tachado en rojo | No respondió (caído, bloquea bots o el dominio cambió) |

El registro de actividad queda en `scraper.log`.

---

## 📁 Archivos

```
INSSSEP.bat                  # Lo que abre el acceso directo "INSSSEP Scraper"
INSTALAR.bat                 # Instala librerías y crea el acceso directo
crear_acceso_directo.ps1     # Crea el acceso directo en el Escritorio
api_noticias.py              # Servidor del panel + control del scraper (PC)
generar_sitio.py             # Genera la página para publicar en internet (lo usa GitHub Actions)
PUBLICAR_EN_GITHUB.bat       # Publica el buscador en internet, gratis (ver la sección ☁️)
publicar_en_github.ps1       # (lo que ejecuta el .bat)
.github/workflows/buscar.yml # Calendario: busca cada 3 horas y publica el sitio
dashboard.html               # Interfaz visual del panel
logo_insssep.png             # Logo (blanco) para el encabezado del panel
insssep_scraper.py           # Motor de búsqueda (palabras clave, filtro de 72 h, historial)
scraper_manual.py            # Búsqueda inmediata por consola
insssep_scraper_con_api.py   # Variante que envía resultados a un servidor remoto
medios.py                    # Lista de medios (editar acá)
config.json                  # Puerto, intervalo, palabras clave y horas máximas (se crea solo)
ultimas_noticias.json        # Última búsqueda (se crea solo)
historial_noticias.json      # Historial de notas vistas (se crea solo, se limpia a los 30 días)
notas_revisadas.json         # Notas ya abiertas, para no repetir trabajo (se crea solo, ~250 KB, se limpia a los 6 días)
sitios_detectados.json       # Qué sitios son WordPress / tienen feed (se crea solo, se renueva cada 7 días)
medios_descubiertos.json     # Medios nuevos que fue mostrando Google Noticias (se crea solo; se puede borrar)
scraper.log                  # Registro de actividad (se crea solo)
```

---

## ⚠️ Notas

- En los sitios que **no** usan WordPress solo se ven las notas que aparecen en su portada: una nota que ya salió de la portada puede no detectarse (Google Noticias ayuda a cubrir parte de eso).
- Se abren muchas notas para comprobar su texto y su fecha; las que no cumplen se descartan: es lo esperado.
- Respetar los términos de uso de cada medio; no hacer búsquedas excesivamente frecuentes.

**Hecho con ❤️ para Resistencia, Chaco**
