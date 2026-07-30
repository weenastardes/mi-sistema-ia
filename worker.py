import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client

# Lectura segura de secretos
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "pruebaprogramacionempresa@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
DEST_EMAIL = os.environ.get("DEST_EMAIL", "pruebaprogramacionempresa@gmail.com")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print(f"🔧 Configuración cargada -> Supabase URL presente: {bool(SUPABASE_URL)} | SMTP Password presente: {bool(SMTP_PASSWORD)}")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

def generar_informe_industrial(tipo_evento, contexto):
    return f"""
==================================================
INFORME TÉCNICO DE SUPERVISIÓN INDUSTRIAL - 24/7
==================================================
TIPO DE EVENTO: {tipo_evento}

DATOS OPERATIVOS:
{contexto}

1. DIAGNÓSTICO PREDICTIVO Y VIDA ÚTIL (RUL):
- El sistema autónomo ha detectado una anomalía cinemática en la línea de producción.
- Estimación RUL: Se requiere intervención técnica antes de llegar al bloqueo total del cabezal.

2. IMPACTO ECONÓMICO:
- Riesgo de parada imprevista con pérdidas estimadas en costes de inactividad de alta criticidad.

3. PLAN DE ACCIÓN INMEDIATO:
- Paso 1: Reducir velocidad operativa de la máquina.
- Paso 2: Despachar equipo de mantenimiento de guardia.
- Paso 3: Revisar telemetría en el panel de control de Streamlit.
==================================================
"""

def enviar_email(remitente, password, destinatario, asunto, cuerpo):
    if not password:
        print("⚠️ No se puede enviar correo: falta SMTP_PASSWORD en los secretos de GitHub.")
        return
    try:
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
        print("✉️ Correo de alerta enviado con éxito.")
    except Exception as e:
        print(f"❌ Error crítico al enviar el correo: {e}")

def ejecutar_inspeccion_autonoma():
    print("🔍 Ejecutando inspección autónoma 24/7...")
    
    capital_actual = 150000.0
    desgaste_cnc = 10.0

    # Leer último estado de Supabase
    if supabase:
        try:
            res = supabase.table("estado_empresa").select("*").order("created_at", desc=True).limit(1).execute()
            if res.data and len(res.data) > 0:
                capital_actual = float(res.data[0].get("capital", 150000.0))
                desgaste_cnc = float(res.data[0].get("desgaste_cnc", 10.0))
                print(f"📥 Estado anterior recuperado de BD -> Capital: {capital_actual} | Desgaste: {desgaste_cnc}")
        except Exception as e:
            print(f"⚠️ Aviso al leer la base de datos: {e}")

    # Simulación industrial orgánica
    ingreso = round(random.uniform(4000.0, 10000.0), 2)
    
    # Incremento de desgaste progresivo (con probabilidad de picos altos para probar las alertas)
    if random.random() < 0.25:
        incremento = random.uniform(15.0, 30.0) # Simula fallo acelerado para probar correo
    else:
        incremento = random.uniform(0.5, 3.0)

    desgaste_cnc = min(100.0, desgaste_cnc + incremento)
    
    if desgaste_cnc >= 100.0:
        desgaste_cnc = 10.0
        print("🛠️ Ciclo completado: Mantenimiento correctivo aplicado automáticamente.")

    coste_operativo = 3500.0 + (desgaste_cnc * 10.0)
    capital_actual += (ingreso - coste_operativo)
    capital_actual = round(capital_actual, 2)

    # Guardar en Supabase
    if supabase:
        try:
            supabase.table("estado_empresa").insert({
                "capital": capital_actual,
                "ingreso": ingreso,
                "desgaste_cnc": round(desgaste_cnc, 2)
            }).execute()
            print(f"💾 Datos insertados correctamente en Supabase.")
        except Exception as e:
            print(f"❌ Error al insertar en Supabase: {e}")
    else:
        print("❌ Error: Supabase no está inicializado.")

    # Disparar alerta por correo si el desgaste cruza el umbral crítico del 75%
    if desgaste_cnc >= 75.0:
        ctx = f"Equipo: Línea CNC\nDesgaste actual: {desgaste_cnc:.1f}%\nCapital disponible: {capital_actual:,.2f} €"
        reporte = generar_informe_industrial("ALERTA CRÍTICA: DESGASTE ELEVADO EN LÍNEA CNC", ctx)
        enviar_email(SMTP_EMAIL, SMTP_PASSWORD, DEST_EMAIL, f"🚨 ALERTA 24/7: Maquinaria en riesgo ({desgaste_cnc:.1f}%)", reporte)

if __name__ == "__main__":
    ejecutar_inspeccion_autonoma()
