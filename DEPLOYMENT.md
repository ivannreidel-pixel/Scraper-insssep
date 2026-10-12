# 🚀 Dónde y cómo se publica el buscador (hosting gratuito)

**Recomendado y ya configurado: GitHub (Pages + Actions).** Costo $0, sin tarjeta, siempre disponible.
Pasos: ver la sección «☁️ Publicar en internet» del [README](README.md) (doble clic en `PUBLICAR_EN_GITHUB.bat`).

## Cómo está armado

```
GitHub Actions  ──cada 3 h──►  python generar_sitio.py  ──►  carpeta site/  ──►  GitHub Pages
 (busca las noticias)          (mismo motor que el panel)     (index.html + datos/*.json)   (la página pública)
        ▲                                                                                 │
        └──────── memoria (historial, notas ya revisadas) recuperada del sitio anterior ◄──┘
```

- `.github/workflows/buscar.yml` es el calendario: corre cada 3 horas, o a mano desde la pestaña **Actions → Run workflow**.
- `generar_sitio.py` busca, escribe `index.html` + `datos/*.json` y guarda la memoria en `estado/*.json`.
- La página es **estática**: no necesita servidor, por eso no se «duerme» ni tiene costo.
- La memoria viaja dentro del propio sitio publicado, así no hace falta base de datos ni almacenamiento aparte.

## Por qué GitHub y no otras opciones

La búsqueda tiene que **salir a ~100 sitios** y tarda varios minutos; el resultado se consulta mucho más de lo que se genera.
Por eso lo más sencillo y gratuito es *generar la página cada 3 horas y servirla estática*.

| Opción | Gratis | Problema para este proyecto |
|---|---|---|
| **GitHub Pages + Actions** (elegida) | Sí, sin tarjeta | Se actualiza cada ~3 h (no al instante); el repositorio es público |
| Render (servicio web gratuito) | Sí, con límites | Se «duerme» tras ~15 min sin visitas (la primera carga tarda ~1 minuto) y el disco se borra al reiniciar: se pierde el historial |
| Hugging Face Spaces | Sí | Se duerme por inactividad y no conserva archivos entre reinicios |
| PythonAnywhere (cuenta gratuita) | Sí | La cuenta gratuita solo permite salir a una lista de sitios autorizados: no puede consultar los medios |
| Oracle Cloud «Always Free» (máquina virtual) | Sí | Pide tarjeta para verificar la cuenta y hay que administrar un servidor (SSH, servicios, seguridad) |
| Railway / Fly.io | No (o con tarjeta) | Ya no tienen un plan gratuito real |
| Tu PC + link de Cloudflare | Sí | Solo funciona con la PC encendida; el link cambia cada vez (es la opción «Generar link» del panel) |

*(Condiciones de los servicios de terceros vigentes al momento de escribir esto; pueden cambiar.)*

## Qué NO tiene la versión publicada

Es de **solo lectura**: no hay «Buscar ahora» ni «Automático». Para eso se usa el panel de la PC (`INSSSEP.bat`), que sigue funcionando igual.
Si en el futuro se necesita un botón «Buscar ahora» en la página pública, hay que sumar un pequeño servicio que dispare el flujo
de GitHub (por ejemplo, un Cloudflare Worker gratuito con un token propio); no está incluido.

## Límites a vigilar

- **Servidores de GitHub en el exterior:** algún medio podría bloquear esas conexiones. El número «Medios consultados» de la página
  permite detectarlo comparándolo con el de la PC. Si fuera un problema serio, la alternativa es correr la búsqueda en la PC y
  subir solo el resultado a GitHub Pages.
- **Calendario:** GitHub puede demorar las ejecuciones programadas unos minutos y pausa los calendarios de repositorios públicos
  sin actividad de 60 días (el flujo se vuelve a habilitar solo en cada ejecución).
- **Es público:** la dirección la puede abrir cualquiera; contiene solo enlaces a notas ya publicadas por los medios.

## Si algo falla

1. Entrá a `https://github.com/TU-USUARIO/buscador-noticias/actions` y abrí la última ejecución: el registro muestra el paso que falló.
2. «Medios consultados» muy bajo → mirar el registro de «Buscar noticias y generar el sitio».
3. La página muestra datos viejos → la última ejecución falló (se conserva la última buena) o todavía no corrió la siguiente.
4. Volver a correr: Actions → *Buscar noticias y publicar* → **Run workflow**.
