import os
import random
import smtplib
import logging
import pytz
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitorSistema:
    def __init__(self):
        # Configuración Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("❌ Faltan credenciales de Supabase")
            raise ValueError("Credenciales de Supabase no configuradas")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Configuración email
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        
        # Zona horaria de Canarias
        self.zona_canarias = pytz.timezone('Atlantic/Canary')
        
        # Parámetros del sistema
        self.capital_inicial = 154000
        self.capital_actual = self.capital_inicial
        self.ingreso_por_iteracion = 8000
        self.numero_registro = 0
        
        # Umbrales para anomalías
        self.umbral_desgaste_alto = 30
        self.umbral_desgaste_bajo = 5
        self.umbral_capital_minimo = 150000
        self.umbral_ingreso_bajo = 1000
        self.umbral_ingreso_alto = 12000

    def obtener_capital_anterior(self):
        """Obtiene el último capital registrado"""
        try:
            response = self.supabase.table('registros').select('capital').order('id', desc=True).limit(1).execute()
            if response.data:
                return response.data[0]['capital']
            return self.capital_inicial
        except Exception as e:
            logger.error(f"Error obteniendo capital anterior: {e}")
            return self.capital_inicial

    def generar_registro(self):
        """Genera un nuevo registro con lógica de negocio mejorada"""
        try:
            # Obtener capital anterior
            capital_anterior = self.obtener_capital_anterior()
            
            # Calcular desgaste CNC con variación realista
            desgaste_base = random.uniform(5, 30)
            
            # Simular situación real: si hay mucho desgaste, el ingreso es menor
            if desgaste_base > 25:
                ingreso = random.uniform(2000, 5000)
            elif desgaste_base > 20:
                ingreso = random.uniform(4000, 7000)
            elif desgaste_base > 15:
                ingreso = random.uniform(6000, 8500)
            else:
                ingreso = random.uniform(8000, 10000)
            
            # Calcular nuevo capital
            nuevo_capital = capital_anterior + ingreso - (desgaste_base * 50)
            
            # Asegurar que el capital no baje demasiado
            if nuevo_capital < 150000:
                nuevo_capital = nuevo_capital + 10000  # Inyección de capital
                logger.info("💉 Inyección de capital aplicada")
            
            # Obtener fecha de Canarias
            fecha_canarias = datetime.now(self.zona_canarias)
            
            registro = {
                'capital': round(nuevo_capital, 2),
                'ingreso': round(ingreso, 2),
                'desgaste_cnc': round(desgaste_base, 2),
                'created_at': fecha_canarias.isoformat()
            }
            
            logger.info(f"📊 Registro generado: {registro}")
            return registro
            
        except Exception as e:
            logger.error(f"Error generando registro: {e}")
            raise

    def verificar_anomalias(self, registro):
        """Verifica si hay anomalías en el registro"""
        anomalias = []
        
        # Verificar desgaste CNC
        if registro['desgaste_cnc'] > self.umbral_desgaste_alto:
            anomalias.append(f"⚠️ ALERTA: Desgaste CNC alto ({registro['desgaste_cnc']:.1f}) - Supera el umbral de {self.umbral_desgaste_alto}")
        elif registro['desgaste_cnc'] < self.umbral_desgaste_bajo:
            anomalias.append(f"ℹ️ INFO: Desgaste CNC bajo ({registro['desgaste_cnc']:.1f}) - Posible mantenimiento excesivo")
        
        # Verificar capital
        if registro['capital'] < self.umbral_capital_minimo:
            anomalias.append(f"⚠️ ALERTA: Capital bajo ({registro['capital']:.2f}) - Por debajo del umbral de {self.umbral_capital_minimo}")
        
        # Verificar ingreso
        if registro['ingreso'] < self.umbral_ingreso_bajo:
            anomalias.append(f"⚠️ ALERTA: Ingreso muy bajo ({registro['ingreso']:.2f}) - Posible problema de producción")
        elif registro['ingreso'] > self.umbral_ingreso_alto:
            anomalias.append(f"ℹ️ INFO: Ingreso excepcionalmente alto ({registro['ingreso']:.2f})")
        
        return anomalias

    def guardar_registro(self):
        """Guarda el registro en Supabase"""
        try:
            registro = self.generar_registro()
            
            # Verificar anomalías
            anomalias = self.verificar_anomalias(registro)
            
            # Insertar en Supabase
            data = self.supabase.table('registros').insert(registro).execute()
            
            logger.info(f"✅ Registro guardado en Supabase")
            logger.info(f"📊 Datos: Capital: {registro['capital']:.2f}, Ingreso: {registro['ingreso']:.2f}, Desgaste: {registro['desgaste_cnc']:.1f}")
            
            # Si hay anomalías, enviar email
            if anomalias:
                logger.warning(f"⚠️ {len(anomalias)} anomalías detectadas")
                for a in anomalias:
                    logger.warning(f"  - {a}")
                
                if self.email_user and self.email_pass:
                    self.enviar_alerta(registro, anomalias)
                else:
                    logger.warning("📧 No se enviará email - credenciales no configuradas")
            
            return True, anomalias
            
        except Exception as e:
            logger.error(f"❌ Error guardando registro: {e}")
            return False, []

    def enviar_alerta(self, registro, anomalias):
        """Envía alerta por email cuando hay anomalías"""
        try:
            if not self.email_user or not self.email_pass:
                logger.warning("📧 Credenciales de email no configuradas")
                return
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_user
            msg['Subject'] = f"🚨 ALERTA - Sistema de Monitoreo {datetime.now(self.zona_canarias).strftime('%Y-%m-%d %H:%M')}"
            
            # Cuerpo del mensaje
            body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: #ff4444; color: white; padding: 10px; border-radius: 5px; }}
                    .registro {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                    .anomalia {{ color: #ff0000; margin: 5px 0; }}
                    .info {{ color: #0066cc; margin: 5px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🚨 Alerta del Sistema de Monitoreo</h2>
                </div>
                
                <div class="registro">
                    <h3>📊 Registro detectado:</h3>
                    <ul>
                        <li><b>Fecha:</b> {registro['created_at']}</li>
                        <li><b>Capital:</b> ${registro['capital']:,.2f}</li>
                        <li><b>Ingreso:</b> ${registro['ingreso']:,.2f}</li>
                        <li><b>Desgaste CNC:</b> {registro['desgaste_cnc']:.1f}%</li>
                    </ul>
                </div>
                
                <div>
                    <h3>⚠️ Anomalías detectadas:</h3>
                    <ul>
            """
            
            for anomalia in anomalias:
                if "ALERTA" in anomalia:
                    body += f'<li class="anomalia">🔴 {anomalia}</li>'
                else:
                    body += f'<li class="info">🟡 {anomalia}</li>'
            
            body += f"""
                    </ul>
                </div>
                
                <div>
                    <p><b>Hora Canarias:</b> {datetime.now(self.zona_canarias).strftime('%H:%M:%S')}</p>
                    <p><b>Revisar el panel de control para más detalles.</b></p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Enviar email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            server.send_message(msg)
            server.quit()
            
            logger.info("📧 Alerta enviada por email correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error enviando alerta: {e}")

def main():
    """Función principal del worker"""
    logger.info("🚀 Iniciando worker de monitoreo...")
    logger.info(f"📍 Zona horaria: Atlantic/Canary")
    logger.info(f"🕐 Hora actual en Canarias: {datetime.now(pytz.timezone('Atlantic/Canary')).strftime('%H:%M:%S')}")
    
    try:
        monitor = MonitorSistema()
        success, anomalias = monitor.guardar_registro()
        
        if success:
            logger.info("✅ Proceso completado exitosamente")
            if anomalias:
                logger.warning(f"⚠️ {len(anomalias)} anomalías detectadas en el registro")
        else:
            logger.error("❌ Error en el proceso")
            
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        raise

if __name__ == "__main__":
    main()
