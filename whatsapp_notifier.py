"""
INSSSEP WhatsApp Notifier
Envía notificaciones a WhatsApp cuando encuentra noticias nuevas
Requiere cuenta de Twilio: https://www.twilio.com
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Configuración de Twilio
TWILIO_ACCOUNT_SID = "tu_account_sid_aqui"
TWILIO_AUTH_TOKEN = "tu_auth_token_aqui"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155552671"  # Número de Twilio
DESTINATARIOS = [
    "whatsapp:+5493625XXXXXX",  # Tu número WhatsApp
    # Agregar más destinatarios si necesita
]


class WhatsAppNotifier:
    """Envía notificaciones por WhatsApp"""
    
    def __init__(self, sid: str = TWILIO_ACCOUNT_SID, token: str = TWILIO_AUTH_TOKEN):
        """
        Inicializa el notificador
        
        Args:
            sid: Twilio Account SID
            token: Twilio Auth Token
        """
        self.sid = sid
        self.token = token
        self.cliente = None
        self.configurado = False
        
        if sid and token and sid != "tu_account_sid_aqui":
            try:
                from twilio.rest import Client
                self.cliente = Client(sid, token)
                self.configurado = True
                logger.info("✓ WhatsApp Notifier configurado")
            except ImportError:
                logger.warning("⚠ Twilio no instalado. Ejecuta: pip install twilio")
            except Exception as e:
                logger.error(f"Error inicializando Twilio: {e}")
    
    def enviar_notificacion(self, resultado: Dict):
        """
        Envía notificación con el resultado de la búsqueda
        
        Args:
            resultado: Dict con {"total_noticias": N, "noticias": [...]}
        """
        if not self.configurado:
            logger.warning("WhatsApp no configurado. Salta notificación.")
            return
        
        try:
            total = resultado.get("total_noticias", 0)
            noticias = resultado.get("noticias", [])
            
            if total == 0:
                mensaje = "📰 No hay noticias INSSSEP en este momento."
            else:
                mensaje = f"📰 {total} noticia{'s' if total > 1 else ''} con INSSSEP encontrada{'s' if total > 1 else ''}:\n\n"
                
                # Agregar primeras 3 noticias
                for noticia in noticias[:3]:
                    titulo = noticia.get("titulo", "Sin título")[:50]
                    medio = noticia.get("medio", "Desconocido")
                    mensaje += f"• {titulo}...\n  ({medio})\n\n"
                
                if total > 3:
                    mensaje += f"... y {total - 3} más"
            
            # Enviar a cada destinatario
            for destinatario in DESTINATARIOS:
                try:
                    self.cliente.messages.create(
                        from_=TWILIO_WHATSAPP_FROM,
                        body=mensaje,
                        to=destinatario
                    )
                    logger.info(f"✓ Notificación enviada a {destinatario}")
                except Exception as e:
                    logger.error(f"Error enviando a {destinatario}: {e}")
        
        except Exception as e:
            logger.error(f"Error en notificación: {e}")
    
    def enviar_notificacion_simple(self, titulo: str, destinatario: str = None):
        """
        Envía notificación simple (para testing)
        
        Args:
            titulo: Mensaje corto
            destinatario: Número WhatsApp (o usa el primero de la lista)
        """
        if not self.configurado:
            logger.warning("WhatsApp no configurado")
            return
        
        dest = destinatario or DESTINATARIOS[0]
        
        try:
            self.cliente.messages.create(
                from_=TWILIO_WHATSAPP_FROM,
                body=titulo,
                to=dest
            )
            logger.info(f"✓ Mensaje enviado: {titulo}")
        except Exception as e:
            logger.error(f"Error: {e}")


# INTEGRACIÓN EN EL SCRAPER
# ======================================
# Agregar esto en insssep_scraper_con_api.py:
#
# 1. En las importaciones:
#    from whatsapp_notifier import WhatsAppNotifier
#
# 2. En __init__ de InsssepScraperConAPI:
#    self.notificador = WhatsAppNotifier()
#
# 3. Después de ejecutar búsqueda:
#    if resultado['total_noticias'] > 0:
#        self.notificador.enviar_notificacion(resultado)


# TESTING
# ======================================
if __name__ == "__main__":
    print("\n🧪 Test de WhatsApp Notifier\n")
    
    print("⚠️  CONFIGURACIÓN REQUERIDA:")
    print("1. Crear cuenta Twilio: https://www.twilio.com/console")
    print("2. Verificar número WhatsApp en Twilio")
    print("3. Editar TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en este archivo")
    print("4. Editar DESTINATARIOS con tu número (+549XXX...)")
    print()
    
    # Crear instancia
    notificador = WhatsAppNotifier()
    
    if not notificador.configurado:
        print("❌ No configurado. Edita las variables en el archivo.\n")
    else:
        print("✅ Notificador configurado\n")
        
        # Test 1: Notificación simple
        print("Enviando test simple...")
        notificador.enviar_notificacion_simple("🧪 Test INSSSEP Scraper")
        
        # Test 2: Con resultado simulado
        print("Enviando notificación con noticias...")
        resultado_test = {
            "total_noticias": 2,
            "noticias": [
                {
                    "titulo": "INSSSEP presenta nuevo programa de salud",
                    "medio": "El Territorio"
                },
                {
                    "titulo": "Beneficiarios INSSSEP reciben turnos para análisis",
                    "medio": "Diario Época"
                }
            ]
        }
        notificador.enviar_notificacion(resultado_test)
        
        print("\n✅ Tests completados\n")
