"""
INSSSEP News Scraper - Versión con envío a API remota
Busca noticias localmente y las envía a un servidor en la nube
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from typing import List, Dict, Optional
import time
import logging

from insssep_scraper import InsssepScraper, MEDIOS_CHACO, PALABRA_CLAVE, RESULTADOS_FILE

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CONFIGURACIÓN - CAMBIAR ESTOS VALORES
SERVIDOR_REMOTO = "http://tu-servidor.com"  # ← Cambiar a tu servidor
API_ENDPOINT = f"{SERVIDOR_REMOTO}/api/noticias/recibir"
GUARDIAS_LOCALES = True  # Si True, también guarda localmente


class InsssepScraperConAPI(InsssepScraper):
    # scrapear_medio / scrapear_todos / _guardar_resultado vienen de InsssepScraper
    def __init__(self, url_servidor: Optional[str] = None):
        super().__init__()
        self.servidor = url_servidor or SERVIDOR_REMOTO
    
    def ejecutar_busqueda_completa(self, on_progress=None) -> Dict:
        """Ejecuta la búsqueda (con filtro de antigüedad y palabras clave) y envía el resultado al servidor"""
        resultado = super().ejecutar_busqueda_completa(on_progress)
        self._enviar_a_servidor(resultado)
        return resultado

    def _enviar_a_servidor(self, resultado: Dict):
        """Envía resultados al servidor remoto"""
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                f"{self.servidor.rstrip('/')}/api/noticias/recibir",
                json=resultado,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Enviado a servidor: {self.servidor}")
            else:
                logger.warning(f"Error al enviar: {response.status_code}")
                logger.warning(f"Respuesta: {response.text}")
        
        except requests.exceptions.ConnectionError:
            logger.warning(f"⚠ No se pudo conectar a {self.servidor}")
            logger.warning("Las noticias se guardarán localmente")
        except Exception as e:
            logger.error(f"Error enviando a servidor: {str(e)}")


class SchedulerConAPI:
    """Scheduler que ejecuta cada 3 horas y envía a servidor"""
    
    def __init__(self, url_servidor: Optional[str] = None):
        self.scraper = InsssepScraperConAPI(url_servidor)
        self.scheduler = BackgroundScheduler()
    
    def tarea_programada(self):
        try:
            self.scraper.ejecutar_busqueda_completa()
        except Exception as e:
            logger.error(f"Error en tarea programada: {str(e)}")
    
    def iniciar(self, ejecutar_ahora: bool = True, intervalo_horas: int = 3):
        """
        Inicia el scheduler
        ejecutar_ahora: ejecutar búsqueda inmediatamente
        intervalo_horas: cada cuántas horas ejecutar (default: 3)
        """
        if ejecutar_ahora:
            logger.info("Ejecutando búsqueda inicial...")
            self.tarea_programada()
        
        self.scheduler.add_job(
            self.tarea_programada,
            'interval',
            hours=intervalo_horas,
            id='insssep_scraper'
        )
        
        self.scheduler.start()
        logger.info(f"✓ Scheduler iniciado. Búsquedas cada {intervalo_horas} horas.")
        logger.info(f"Servidor remoto: {self.scraper.servidor}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler detenido")
            self.scheduler.shutdown()


if __name__ == "__main__":
    import sys
    
    # Permite pasar servidor como argumento: python script.py http://tu-servidor.com
    url_servidor = sys.argv[1] if len(sys.argv) > 1 else None
    
    scheduler = SchedulerConAPI(url_servidor)
    scheduler.iniciar(ejecutar_ahora=True, intervalo_horas=3)
