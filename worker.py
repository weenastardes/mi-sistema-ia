import os
import random
import logging
import pytz
import time
import threading
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Servidor HTTP ultraligero para mantener activo el Web Service gratuito en Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Worker y Web Service activos y funcionando correctamente!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    logger.info(f"🌐 Servidor web secundario escuchando en el puerto {port}")
    server.serve_forever()

class MonitorSistema:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("❌ Faltan credenciales de Supabase")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        self.email_user = os.getenv('EMAIL_USER')
        self.resend_key = os.getenv('RESEND_API_KEY')
        self.zona_canarias = pytz.timezone('Atlantic/Canary')
        
        # Umbrales ajustados para evitar falsos positivos constantes
        self.umbral_desgaste_alto = 50.0  # Subido a 50 para que salte solo en desgaste serio
        self.umbral_desgaste_bajo = 5.0
        self.umbral_capital_minimo = 145000.0
        self.umbral_ingreso_bajo = 1200.0
        self.umbral_ingreso_alto = 9000.0  # Para detectar picos positivos de ganancia
        
        # Control de tiempo para evitar spam de correos (Cooldown de 30 minutos)
        self.ultimo_correo_enviado = None
        self.cooldown_minutos = 30

    def obtener_capital_anterior(self):
        try:
            response = self.supabase.table('registros').select('capital').order('id', desc=True).limit(1).execute()
            if response.data:
                return response.data[0]['capital']
            return 154000
        except:
            return 154000

    def generar_registro(self):
        capital_anterior = self.obtener_capital_anterior()
        
        desgaste_base = random.uniform(5, 55)
        
        if desgaste_base > 40:
            ingreso = random.uniform(1500, 3500)
        elif desgaste_base > 25:
            ingreso = random.uniform(3000, 6000)
        elif desgaste_base > 20:
            ingreso = random.uniform(5000, 7500)
        elif desgaste_base > 15:
            ingreso = random.uniform(6500, 8500)
        else:
            ingreso = random.uniform(8000, 10000)
        
        nuevo_capital = capital_anterior + ingreso - (desgaste_base * 40)
        
        if nuevo_capital < 150000:
            nuevo_capital = nuevo_capital + 10000
        
        fecha_canarias = datetime.now(self.zona_canarias).strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'capital': round(nuevo_capital, 2),
            'ingreso': round(ingreso, 2),
            'desgaste_cnc': round(desgaste_base, 2),
            'created_at': fecha_canarias
        }

    def verificar_anomalias(self, registro):
        anomalias = []
        
        # Solo consideramos anomalías de peso real para notificaciones
        if registro['desgaste_cnc'] > self.umbral_desgaste_alto:
            anomalias.append(f"⚠️ ALERTA CRÍTICA: Desgaste CNC elevado ({registro['desgaste_cnc']:.1f}%)")
        
        if registro['capital'] < self.umbral_capital_minimo:
            anomalias.append(f"⚠️ ALERTA CRÍTICA: Capital bajo operativo ({registro['capital']:,.2f} €)")
        
        if registro['ingreso'] < self.umbral_ingreso_bajo:
            anomalias.append(f"📉 AVISO: Ingreso bajo registrado ({registro['ingreso']:,.2f} €)")
        elif registro['ingreso'] > self.umbral_ingreso_alto:
            anomalias.append(f"📈 NOTICIA POSITIVA: ¡Pico de ingresos alto! ({registro['ingreso']:,.2f} €)")
        
        return anomalias

    def guardar_registro(self):
        try:
            registro = self.generar_registro()
            anomalias = self.verificar_anomalias(registro)
            
            self.supabase.table('registros').insert(registro).execute()
            
            logger.info(f"✅ Registro guardado: Capital: {registro['capital']:,.2f}, Ingreso: {registro['ingreso']:,.2f}, Desgaste: {registro['desgaste_cnc']:.1f}%")
            
            if anomalias and self.email_user and self.resend_key:
                # Comprobación de Cooldown: ¿Ha pasado suficiente tiempo desde el último correo?
                ahora = datetime.now(self.zona_canarias)
                debe_enviar = False
                
                if self.ultimo_correo_enviado is None:
                    debe_enviar = True
                else:
                    tiempo_transcurrido = (ahora - self.ultimo_correo_enviado).total_seconds() / 60
                    if tiempo_transcurrido >= self.cooldown_minutos:
                        debe_enviar = True
                    else:
                        logger.info(f"⏳ Omitiendo envío de correo por Cooldown ({tiempo_transcurrido:.1f}m transcurridos de {self.cooldown_minutos}m requeridos).")

                if debe_enviar:
                    logger.info("🚨 ¡Anomalías detectadas y periodo de espera cumplido! Enviando correo...")
                    self.enviar_alerta(registro, anomalias)
                    self.ultimo_correo_enviado = ahora
            elif anomalias:
                logger.warning(f"⚠️ Hay anomalías ({len(anomalias)}) pero faltan credenciales de email.")
            
            return True, anomalias
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False, []

    def enviar_alerta(self, registro, anomalias):
        try:
            lista_html = "".join([f"<li>{a}</li>" for a in anomalias])
            
            html_content = f"""
            <h2>🏭 Reporte Inteligente - Industrias 24/7</h2>
            <p><b>Fecha:</b> {registro['created_at']}</p>
            <p><b>Capital Actual:</b> ${registro['capital']:,.2f}</p>
            <p><b>Ingreso del Ciclo:</b> ${registro['ingreso']:,.2f}</p>
            <p><b>Desgaste CNC:</b> {registro['desgaste_cnc']:.1f}%</p>
            <h3>🔍 Detalles del Evento:</h3>
            <ul>{lista_html}</ul>
            <p style="color: #666; font-size: 12px;">Este es un aviso automatizado. Se aplicó un filtro de intervalo para evitar notificaciones repetitivas.</p>
            """

            headers = {
                "Authorization": f"Bearer {self.resend_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "from": "onboarding@resend.dev",
                "to": self.email_user,
                "subject": f"🏭 Reporte Destacado Industrias {datetime.now(self.zona_canarias).strftime('%Y-%m-%d %H:%M')}",
                "html": html_content
            }

            response = requests.post("https://api.resend.com/emails", json=data, headers=headers)
            
            if response.status_code == 200:
                logger.info("📧 Alerta enviada exitosamente a través de Resend")
            else:
                logger.error(f"❌ Error al enviar con Resend: {response.text}")

        except Exception as e:
            logger.error(f"❌ Error email: {e}")

def main():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    logger.info("🚀 Iniciando worker en bucle continuo...")
    logger.info(f"📍 Zona: Atlantic/Canary - Hora inicio: {datetime.now(pytz.timezone('Atlantic/Canary')).strftime('%H:%M:%S')}")
    
    INTERVALO_SEGUNDOS = 30
    
    try:
        monitor = MonitorSistema()
    except Exception as e:
        logger.error(f"❌ Error crítico al inicializar el monitor: {e}")
        return

    while True:
        try:
            logger.info("--- Ejecutando ciclo de monitorización ---")
            success, anomalias = monitor.guardar_registro()
            
            if success:
                if anomalias:
                    logger.warning(f"⚠️ Ciclo completado con {len(anomalias)} anomalías.")
                else:
                    logger.info("✅ Ciclo completado sin incidencias.")
            else:
                logger.error("❌ Falló el almacenamiento de este ciclo.")
                
        except Exception as e:
            logger.error(f"❌ Error inesperado en el bucle: {e}")
            
        logger.info(f"⏳ Esperando {INTERVALO_SEGUNDOS} segundos para el siguiente ciclo...\n")
        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    main()
