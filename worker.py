import os
import random
import smtplib
import logging
import pytz
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MonitorSistema:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("❌ Faltan credenciales de Supabase")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        self.zona_canarias = pytz.timezone('Atlantic/Canary')
        
        # Umbrales para anomalías
        self.umbral_desgaste_alto = 30
        self.umbral_desgaste_bajo = 5
        self.umbral_capital_minimo = 150000
        self.umbral_ingreso_bajo = 1000

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
        
        # Ampliado hasta 55 para garantizar que salten alertas de desgaste alto y probar los correos
        desgaste_base = random.uniform(5, 55)
        
        # Ajuste de ingresos: se garantiza un suelo mínimo incluso en desgaste alto para evitar ceros
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
        
        # Formato de texto plano con la hora exacta de Canarias (sin desfase UTC)
        fecha_canarias = datetime.now(self.zona_canarias).strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'capital': round(nuevo_capital, 2),
            'ingreso': round(ingreso, 2),
            'desgaste_cnc': round(desgaste_base, 2),
            'created_at': fecha_canarias
        }

    def verificar_anomalias(self, registro):
        anomalias = []
        
        if registro['desgaste_cnc'] > self.umbral_desgaste_alto:
            anomalias.append(f"⚠️ ALERTA: Desgaste CNC alto ({registro['desgaste_cnc']:.1f})")
        elif registro['desgaste_cnc'] < self.umbral_desgaste_bajo:
            anomalias.append(f"ℹ️ INFO: Desgaste CNC bajo ({registro['desgaste_cnc']:.1f})")
        
        if registro['capital'] < self.umbral_capital_minimo:
            anomalias.append(f"⚠️ ALERTA: Capital bajo ({registro['capital']:.2f})")
        
        if registro['ingreso'] < self.umbral_ingreso_bajo:
            anomalias.append(f"⚠️ ALERTA: Ingreso muy bajo ({registro['ingreso']:.2f})")
        
        return anomalias

    def guardar_registro(self):
        try:
            registro = self.generar_registro()
            anomalias = self.verificar_anomalias(registro)
            
            self.supabase.table('registros').insert(registro).execute()
            
            logger.info(f"✅ Registro guardado: Capital: {registro['capital']:.2f}, Ingreso: {registro['ingreso']:.2f}, Desgaste: {registro['desgaste_cnc']:.1f}")
            
            if anomalias and self.email_user and self.email_pass:
                logger.info("🚨 ¡Anomalías detectadas! Intentando enviar correo...")
                self.enviar_alerta(registro, anomalias)
            else:
                logger.warning(f"⚠️ Hay anomalías ({len(anomalias)}) o faltan credenciales. User: {bool(self.email_user)}, Pass: {bool(self.email_pass)}")
            
            return True, anomalias
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False, []

    def enviar_alerta(self, registro, anomalias):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_user
            msg['Subject'] = f"🚨 ALERTA Sistema {datetime.now(self.zona_canarias).strftime('%Y-%m-%d %H:%M')}"
            
            body = f"""
            <h2>🚨 Alerta del Sistema</h2>
            <p><b>Fecha:</b> {registro['created_at']}</p>
            <p><b>Capital:</b> ${registro['capital']:,.2f}</p>
            <p><b>Ingreso:</b> ${registro['ingreso']:,.2f}</p>
            <p><b>Desgaste CNC:</b> {registro['desgaste_cnc']:.1f}%</p>
            <h3>⚠️ Anomalías:</h3>
            <ul>
            """
            for a in anomalias:
                body += f"<li>{a}</li>"
            body += "</ul>"
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            server.send_message(msg)
            server.quit()
            
            logger.info("📧 Alerta enviada")
        except Exception as e:
            logger.error(f"❌ Error email: {e}")

def main():
    logger.info("🚀 Iniciando worker...")
    logger.info(f"📍 Zona: Atlantic/Canary - Hora: {datetime.now(pytz.timezone('Atlantic/Canary')).strftime('%H:%M:%S')}")
    
    try:
        monitor = MonitorSistema()
        success, anomalias = monitor.guardar_registro()
        
        if success:
            logger.info("✅ Proceso completado")
            if anomalias:
                logger.warning(f"⚠️ {len(anomalias)} anomalías")
        else:
            logger.error("❌ Error en el proceso")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    main()
