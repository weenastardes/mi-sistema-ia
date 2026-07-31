import os
import random
import time
from datetime import datetime, timedelta
from supabase import create_client, Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitorSistema:
    def __init__(self):
        # Configuración Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Configuración email
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        
        # Parámetros del sistema
        self.capital_inicial = 154000
        self.capital_actual = self.capital_inicial
        self.ingreso_por_iteracion = 8000
        
        # Umbrales para anomalías
        self.umbral_desgaste_alto = 30
        self.umbral_desgaste_bajo = 5
        self.umbral_capital_minimo = 150000

    def generar_registro(self):
        """Genera un nuevo registro con lógica de negocio mejorada"""
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
        
        # Actualizar capital
        self.capital_actual = self.capital_actual + ingreso - (desgaste_base * 50)
        
        # Asegurar que el capital no baje demasiado
        if self.capital_actual < 150000:
            self.capital_actual = self.capital_actual + 10000  # Inyección de capital
        
        return {
            'capital': round(self.capital_actual, 2),
            'ingreso': round(ingreso, 2),
            'desgaste_cnc': round(desgaste_base, 2)
        }

    def verificar_anomalias(self, registro):
        """Verifica si hay anomalías en el registro"""
        anomalias = []
        
        # Verificar desgaste CNC
        if registro['desgaste_cnc'] > self.umbral_desgaste_alto:
            anomalias.append(f"ALERTA: Desgaste CNC alto ({registro['desgaste_cnc']:.1f}) - Supera el umbral de {self.umbral_desgaste_alto}")
        elif registro['desgaste_cnc'] < self.umbral_desgaste_bajo:
            anomalias.append(f"INFORMACIÓN: Desgaste CNC bajo ({registro['desgaste_cnc']:.1f}) - Posible mantenimiento excesivo")
        
        # Verificar capital
        if registro['capital'] < self.umbral_capital_minimo:
            anomalias.append(f"ALERTA: Capital bajo ({registro['capital']:.2f}) - Por debajo del umbral de {self.umbral_capital_minimo}")
        
        # Verificar ingreso
        if registro['ingreso'] < 1000:
            anomalias.append(f"ALERTA: Ingreso muy bajo ({registro['ingreso']:.2f}) - Posible problema de producción")
        elif registro['ingreso'] > 12000:
            anomalias.append(f"INFORMACIÓN: Ingreso excepcionalmente alto ({registro['ingreso']:.2f})")
        
        return anomalias

    def guardar_registro(self):
        """Guarda el registro en Supabase"""
        try:
            registro = self.generar_registro()
            
            # Verificar anomalías
            anomalias = self.verificar_anomalias(registro)
            
            # Insertar en Supabase
            data, count = self.supabase.table('registros').insert(registro).execute()
            
            logger.info(f"Registro guardado: {registro}")
            
            # Si hay anomalías, enviar email
            if anomalias and self.email_user:
                self.enviar_alerta(registro, anomalias)
            
            return True, anomalias
            
        except Exception as e:
            logger.error(f"Error guardando registro: {e}")
            return False, []

    def enviar_alerta(self, registro, anomalias):
        """Envía alerta por email cuando hay anomalías"""
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_user  # Enviar a sí mismo
            msg['Subject'] = f"🚨 ALERTA - Sistema de Monitoreo {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Cuerpo del mensaje
            body = f"""
            <h2>🚨 Alerta del Sistema de Monitoreo</h2>
            
            <h3>Registro detectado:</h3>
            <ul>
                <li><b>Capital:</b> ${registro['capital']:,.2f}</li>
                <li><b>Ingreso:</b> ${registro['ingreso']:,.2f}</li>
                <li><b>Desgaste CNC:</b> {registro['desgaste_cnc']:.1f}%</li>
            </ul>
            
            <h3>⚠️ Anomalías detectadas:</h3>
            <ul>
            """
            
            for anomalia in anomalias:
                body += f"<li>{anomalia}</li>"
            
            body += """
            </ul>
            
            <p>Fecha: {}</p>
            <p>Revisar el panel de control para más detalles.</p>
            """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            msg.attach(MIMEText(body, 'html'))
            
            # Enviar email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            server.send_message(msg)
            server.quit()
            
            logger.info("Alerta enviada por email")
            
        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")

def main():
    """Función principal del worker"""
    logger.info("Iniciando worker de monitoreo...")
    
    monitor = MonitorSistema()
    success, anomalias = monitor.guardar_registro()
    
    if success:
        logger.info("✅ Registro guardado exitosamente")
        if anomalias:
            logger.warning(f"⚠️ {len(anomalias)} anomalías detectadas")
            for a in anomalias:
                logger.warning(f"  - {a}")
    else:
        logger.error("❌ Error guardando el registro")

if __name__ == "__main__":
    main()
