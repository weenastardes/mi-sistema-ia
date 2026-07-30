import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from supabase import create_client

# ---------------------------------------------------------
# LECTURA DE SECRETOS DE ENTORNO
# ---------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "pruebaprogramacionempresa@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
DEST_EMAIL = os.environ.get("DEST_EMAIL", "pruebaprogramacionempresa@gmail.com")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

def consultar_gemini(api_key, tipo_evento, contexto):
    if not api_key:
        return "Error: API Key de Gemini no configurada."
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
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error consultando Gemini: {e}"

def enviar_email(remitente, password, destinatario, asunto, cuerpo):
    if not password:
        print("⚠️ No se puede enviar correo: falta SMTP_PASSWORD.")
        return
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
    print("🔍 Iniciando inspección autónoma y conectando a la BD...")
    
    capital_actual = 150000.0
    desgaste_cnc = 10.0

    # Leer el último estado guardado en la base de datos
    if supabase:
        try:
            res = supabase.table("estado_empresa").select("*").order("created_at", desc=True).limit(1).execute()
            if res.data:
                capital_actual = float(res.data[0].get("capital", 150000.0))
                desgaste_cnc = float(res.data[0].get("desgaste_cnc", 10.0))
        except Exception as e:
            print(f"⚠️ Aviso al leer BD: {e}")

    # Simulación de ciclo idéntica a la de la app
    ingreso = random.randint(3000, 12000)
    probabilidad = random.random()

    if probabilidad < 0.20:
        desgaste_cnc = min(100.0, desgaste_cnc + random.uniform(15.0, 25.0))
    else:
        desgaste_cnc = min(100.0, desgaste_cnc + random.uniform(0.5, 2.0))

    capital_actual += (ingreso - 4000.0)

    # Guardar SIEMPRE en Supabase
    if supabase:
        try:
            supabase.table("estado_empresa").insert({
                "capital": capital_actual,
                "ingreso": ingreso,
                "desgaste_cnc": desgaste_cnc
            }).execute()
            print("💾 Datos registrados exitosamente en Supabase!")
        except Exception as e:
            print(f"❌ Error al guardar en BD: {e}")
    else:
        print("❌ Error: No hay conexión configurada con Supabase.")

    # Alerta por Gemini si el desgaste es crítico
    if desgaste_cnc >= 75.0:
        ctx = f"Equipo: Línea CNC\nDesgaste actual: {desgaste_cnc:.1f}%\nCapital disponible: {capital_actual:,.2f} €"
        reporte = consultar_gemini(GEMINI_API_KEY, "ALERTA PREDICTIVA: DESGASTE ELEVADO EN MAQUINARIA", ctx)
        enviar_email(SMTP_EMAIL, SMTP_PASSWORD, DEST_EMAIL, f"🚨 AUTÓNOMO 24/7: Fallo inminente (Desgaste {desgaste_cnc:.1f}%)", reporte)
        print("✉️ Correo de alerta enviado.")

if __name__ == "__main__":
    ejecutar_inspeccion_autonoma()
