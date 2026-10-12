"""
Lista única de medios de Chaco a scrapear.
La usan insssep_scraper.py, insssep_scraper_con_api.py y scraper_manual.py.
Para agregar o quitar un medio, editar SOLO este archivo.
"""

# (nombre, url, zona)
_MEDIOS = [
    # --- Resistencia y alcance provincial ---
    ("Alerta Urbana", "https://alertaurbana.com.ar", "Resistencia/Provincial"),
    ("Chaco Ahora", "https://chacoahora.com", "Resistencia/Provincial"),
    ("Chaco Día por Día", "https://chacodiapordia.com", "Resistencia/Provincial"),
    ("Chaco TV", "https://chacotv.com", "Resistencia/Provincial"),
    ("Ciudad Televisión", "https://ciudadtv.ar", "Resistencia/Provincial"),
    ("DataChaco", "https://www.datachaco.com", "Resistencia/Provincial"),
    ("Diario 22", "https://www.diario22.ar", "Resistencia/Provincial"),
    ("Diario Chaco", "https://www.diariochaco.com", "Resistencia/Provincial"),
    ("Diario Norte", "https://www.diarionorte.com", "Resistencia/Provincial"),
    ("Diario Primera Línea", "https://diarioprimeralinea.com.ar", "Resistencia/Provincial"),
    ("Diario TAG", "https://www.diariotag.com", "Resistencia/Provincial"),
    ("El Diario de la Región", "https://www.eldiariodelaregion.com.ar", "Resistencia/Provincial"),
    ("Entretiempo", "https://entretiempo.info", "Resistencia/Provincial"),
    ("Infoqom", "https://infoqom.com.ar", "Resistencia/Provincial"),
    ("La Radio 104.7", "https://laradio1047.com.ar", "Resistencia/Provincial"),
    ("Diario La Voz del Chaco", "https://www.diariolavozdelchaco.com", "Resistencia/Provincial"),
    ("Like Informativo", "https://likeinformativo.com", "Resistencia/Provincial"),
    ("Mascontenidos", "https://mascontenidos.net", "Resistencia/Provincial"),
    ("Norte Grande Federal", "https://ngfederal.ar", "Resistencia/Provincial"),
    ("Noticiero 9", "https://www.noticiero9.com.ar", "Resistencia/Provincial"),
    ("Canal 9 Nordeste", "https://canal9nordeste.com.ar", "Resistencia/Provincial"),
    ("Nova Chaco", "https://www.novachaco.com", "Resistencia/Provincial"),
    ("Radio Facundo Quiroga", "https://www.facundoquiroga.com", "Resistencia/Provincial"),
    ("FM Gualamba", "https://fmgualamba.com.ar", "Resistencia/Provincial"),
    ("Radio Nordeste", "https://www.radionordeste.ar", "Resistencia/Provincial"),
    ("Reporte Chaco", "https://reportechaco.com", "Resistencia/Provincial"),
    ("TN24", "https://tn24.com.ar", "Resistencia/Provincial"),
    ("Vía Chaco", "https://viapais.com.ar/resistencia", "Resistencia/Provincial"),
    ("Chaco On Line", "https://chacoonline.com.ar", "Resistencia/Provincial"),
    ("Chaco Todo el Día", "https://chacotodoeldia.com", "Resistencia/Provincial"),
    ("Noticias Digital Chaco", "https://noticiasdigitalchaco.com", "Resistencia/Provincial"),
    ("Diario YA", "https://www.diarioya.ar", "Resistencia/Provincial"),
    ("NoticieroCHACO", "https://noticierochaco.com", "Resistencia/Provincial"),
    ("Radio Natagalá 94.7", "https://radionatagala.com", "Resistencia/Provincial"),
    ("Radio Universidad 91.1", "https://www.radiouniversidad911.com.ar", "Resistencia/Provincial"),
    ("Radio 6 de Enero", "https://www.radio6deenero.com", "Resistencia/Provincial"),
    ("Master FM 89.9", "https://master.com.ar", "Resistencia/Provincial"),
    ("Radio Provincia del Chaco 101.5", "https://radioprovinciadelchaco.com.ar", "Resistencia/Provincial"),
    ("El Difusor", "https://eldifusor.com", "Resistencia/Provincial"),
    ("Nuestro Chaco", "https://nuestrochaco.com", "Resistencia/Provincial"),
    ("SoloChaco", "https://solochaco.com", "Resistencia/Provincial"),
    ("TodoChaco", "https://todochaco.com.ar", "Resistencia/Provincial"),
    ("Chaco en Red", "https://chacoenred.com.ar", "Resistencia/Provincial"),
    ("Todo Chaco Info", "https://todochacoinfo.com.ar", "Resistencia/Provincial"),
    ("Portal Noticias Ahora", "https://portalnoticiasahora.com.ar", "Resistencia/Provincial"),
    ("Qué Pasa Chaco", "https://quepasachaco.com.ar", "Resistencia/Provincial"),
    ("Nuevo Chaco", "https://nuevochaco.com", "Resistencia/Provincial"),
    ("Noticias Chaco", "https://www.noticiaschaco.com", "Resistencia/Provincial"),
    ("Agroperfiles", "https://agroperfiles.com.ar", "Resistencia/Provincial"),
    ("Radio Primera", "https://www.radioprimera.com.ar", "Resistencia/Provincial"),
    ("Radio Nacional Resistencia", "https://www.radionacional.com.ar/resistencia/", "Resistencia/Provincial"),
    ("Angau Noticias (satírico)", "https://www.angaunoticias.com.ar", "Resistencia/Provincial"),
    ("Libertad Digital", "https://www.libertaddigital.com.ar", "Resistencia/Provincial"),

    # --- Presidencia Roque Sáenz Peña ---
    ("Eco Chaqueño", "https://ecochaqueno.com.ar", "Sáenz Peña"),
    ("El Diario (Sáenz Peña)", "https://eldiariosp.com.ar", "Sáenz Peña"),
    ("El Norteño", "https://www.xn--elnorteo-j3a.com.ar", "Sáenz Peña"),
    ("Eres Chaco", "https://www.ereschaco.com", "Sáenz Peña"),
    ("La Red Noticias", "https://larednoticias.com.ar", "Sáenz Peña"),
    ("Opción de Noticias", "https://opciondenoticias.com.ar", "Sáenz Peña"),
    ("Periodismo 365", "https://www.periodismo365.com", "Sáenz Peña"),
    ("Portal de los Pueblos", "https://portaldelospueblos.com.ar", "Sáenz Peña"),
    ("Primero Chaco", "https://primerochaco.com", "Sáenz Peña"),
    ("SP Noticias", "https://spnoticias.com.ar", "Sáenz Peña"),
    ("Sáenz Peña Noticias", "https://saenzpena.com", "Sáenz Peña"),
    ("TodoNEA", "https://www.todonea.com", "Sáenz Peña"),
    ("Infotermal", "https://infotermal.com", "Sáenz Peña"),

    # --- Villa Ángela ---
    ("Es Chaco", "https://eschaco.com", "Villa Ángela"),
    ("FM Manantial 89.3", "https://fmmanantial893.com", "Villa Ángela"),
    ("Gente del Pueblo", "https://gentedepueblo.com", "Villa Ángela"),
    ("La 21 Radio", "https://la21radio.com.ar", "Villa Ángela"),
    ("Villa Ángela Hoy", "https://villaangelahoy.com", "Villa Ángela"),
    ("Diario Villa Ángela", "https://diariovillaangela.com.ar", "Villa Ángela"),
    ("FM MagaLih 94.1", "https://magalihfm.com.ar", "Villa Ángela"),
    ("Villa Ángela Prensa", "https://villaangelaprensa.com.ar", "Villa Ángela"),

    # --- Santa Sylvina ---
    ("Diario Santa Sylvina", "https://diariosantasylvina.com.ar", "Santa Sylvina"),

    # --- Charata y sudoeste ---
    ("CharataChaco.net", "https://charatachaco.net", "Charata"),
    ("Charata.com", "https://charata.com", "Charata"),
    ("El Corresponsal", "https://elcorresponsal.com.ar", "Charata"),
    ("Movilero", "https://movilero.com.ar", "Charata"),
    ("Radio Charata", "https://radiocharata.com.ar", "Charata"),
    ("Radio Mocoví", "https://radiomocovi.com.ar", "Charata"),
    ("STC Chaco", "https://stcchaco.com", "Charata"),
    ("Cadena Pueblo Noticias", "https://cadenapueblonoticias.com.ar", "Charata"),
    ("Red Televisión", "https://redtvsrl.com.ar/servicios/television/", "Charata"),

    # --- Corzuela ---
    ("Corzuela en la Web", "https://corzuelaenlaweb.com.ar", "Corzuela"),

    # --- General José de San Martín ---
    ("El Rey del Deporte", "https://elreydeldeporte.com.ar", "San Martín"),

    # --- Juan José Castelli e Impenetrable ---
    ("Castelli en Línea", "https://www.castellienlinea.com.ar", "Castelli"),
    ("Diario Castelli", "https://diariocastelli.com", "Castelli"),
    ("Pórtico Noticias", "https://porticonoticias.com", "Castelli"),
    ("El Chaco Impenetrable", "https://elchacoimpenetrable.com", "Castelli"),

    # --- Las Breñas ---
    ("Las Breñas Digital", "https://lasbrenasdigital.com.ar", "Las Breñas"),

    # --- Machagai ---
    ("Televisión y Radio", "https://www.televisionyradio.com.ar", "Machagai"),
    ("Radio Master 102.5", "https://www.radiomasterfm.com.ar", "Machagai"),

    # --- Quitilipi ---
    ("La Voz de Quitilipi", "https://lavozdequitilipi.com.ar", "Quitilipi"),
    ("Quitilipi.com.ar", "https://quitilipi.com.ar", "Quitilipi"),

    # --- Tres Isletas ---
    ("FM Génesis Tres Isletas", "https://genesistresisletas.com.ar", "Tres Isletas"),

    # --- Barranqueras ---
    ("Noticias del Paraná", "https://noticiasdelparana.com.ar", "Barranqueras"),
    ("Barranqueras Online", "https://barranquerasonline.com.ar", "Barranqueras"),
    ("Info Barranqueras", "https://infobarranqueras.com.ar", "Barranqueras"),

    # --- Margarita Belén ---
    ("Margarita Belén", "https://margaritabelen.com", "Margarita Belén"),

    # --- Presidencia de la Plaza ---
    ("Diario Plaza 109", "https://diarioplaza109.com", "Presidencia de la Plaza"),

    # --- General Pinedo ---
    ("Pinedo Noticias", "https://www.pinedonoticias.com.ar", "General Pinedo"),

    # --- Fuentes oficiales (con opciones propias) ---
    # "paginas": cuántas páginas del listado leer (?page=2, ?page=3...)
    # "patron":  solo se consideran notas las direcciones que cumplan esta expresión regular
    # "extra_urls": otras páginas con listados de notas
    ("Gobierno del Chaco", "https://chaco.gob.ar/noticias", "Gobierno", {"paginas": 8}),
    ("INSSSEP (sitio oficial)", "https://www.insssep.gob.ar/", "Oficial",
     {"patron": r"/Publicaciones/View/", "extra_urls": ["/Publicaciones"]}),
]

# Cada medio: (nombre, url, zona) y, opcionalmente, un diccionario de opciones como cuarto elemento.
MEDIOS_CHACO = [
    {"nombre": n, "url": u, "zona": z, "buscar_en": "noticias", **(extra[0] if extra else {})}
    for n, u, z, *extra in _MEDIOS
]
