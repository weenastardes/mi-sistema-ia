import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# ---------------------------------------------------------
# LECTURA DE SECRETOS DE ENTORNO
# ---------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "pruebaprogramacionempresa@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
DEST_EMAIL = os.environ.get("DEST_EMAIL", "pruebaprogramacionempresa@gmail.com")

def consultar_gemini(api_key, tipo_evento, contexto):
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Eres el Director Técnico e Inteligencia Artificial Supervisora de la empresa Industrias Innovación S.L.
    
    TIPO DE INCIDENCIA DETECTADA: {tipo_evento}
    DATOS OPERATIVOS EN TIEMPO REAL:
    {contexto}

    REQUERIMIENTOS DEL INFORME:
    1. Diagnóstico Predictivo y estimación de Vida Útil Restante (RUL).
    2. Análisis de Impacto Económico.
    3. Plan de Acción Inmediato (3 pasos ejecutivos).
    4. Tono: Profesional, directo y urgente.
    """
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error consultando Gemini: {e}"

def enviar_email(remitente, password, destinatario, asunto, cuerpo):
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(remitente, password)
    server.sendmail(remitente, destinatario, msg.as_string())
    server.quit()

def ejecutar_inspeccion_autonoma():
    print("🔍 Iniciando inspección autónoma de sensores y finanzas...")
    
    probabilidad = random.random()
    
    # 1. Escenario de Avería (20% de probabilidad)
    if probabilidad < 0.20:
        print("🚨 Anomalía crítica detectada en maquinaria!")
        maq = "Línea de Corte Láser CNC"
        desgaste = random.uniform(80.0, 96.0)
        temp = random.uniform(85.0, 110.0)
        ctx = f"Equipo: {maq}\nDesgaste: {desgaste:.1f}%\nTemperatura: {temp:.1f} °C\nCosto Preventivo: 4.000 €\nCosto Parada Catastrófica: 32.000 €"
        
        reporte = consultar_gemini(GEMINI_API_KEY, "ALERTA PREDICTIVA: FALLO CRÍTICO EN MAQUINARIA", ctx)
        enviar_email(SMTP_EMAIL, SMTP_PASSWORD, DEST_EMAIL, f"🚨 AUTÓNOMO 24/7: Fallo inminente en {maq}", reporte)
        print("✉️ Correo de alerta enviado exitosamente.")

    # 2. Escenario de Pico Financiero (15% de probabilidad)
    elif probabilidad > 0.85:
        print("💰 Pico de ventas detectado!")
        ingreso = random.randint(45000, 85000)
        ctx = f"Ingreso Extraordinario Registrado: {ingreso:,.2f} €"
        
        reporte = consultar_gemini(GEMINI_API_KEY, "INFORME FINANCIERO: PICO DE VENTAS", ctx)
        enviar_email(SMTP_EMAIL, SMTP_PASSWORD, DEST_EMAIL, f"🚀 AUTÓNOMO 24/7: Pico de Ventas ({ingreso:,.2f} €)", reporte)
        print("✉️ Correo financiero enviado exitosamente.")
    else:
        print("🟢 Inspección completada: Todos los sistemas operan dentro de parámetros normales.")

if __name__ == "__main__":
    if GEMINI_API_KEY and SMTP_PASSWORD:
        ejecutar_inspeccion_autonoma()
    else:
        print("⚠️ Faltan las variables de entorno (GEMINI_API_KEY o SMTP_PASSWORD).")
