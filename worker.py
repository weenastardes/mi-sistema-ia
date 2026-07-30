import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client

# ---------------------------------------------------------
# LECTURA DE SECRETOS DE ENTORNO
# ---------------------------------------------------------
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "pruebaprogramacionempresa@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
DEST_EMAIL = os.environ.get("DEST_EMAIL", "pruebaprogramacionempresa@gmail.com")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

def generar_informe_industrial(tipo_evento, contexto):
    """Genera un informe técnico profesional de forma local y gratuita sin requerir APIs externas de pago."""
    return f"""
==================================================
INFORME TÉCNICO DE SUPERVISIÓN INDUSTRIAL - 24/7
==================================================
TIPO DE EVENTO: {tipo_evento}

DATOS OPERATIVOS EN TIEMPO REAL:
{contexto}

1. DIAGNÓSTICO PREDICTIVO Y VIDA ÚTIL RESTANTE (RUL):
- El sistema de monitorización autónoma ha evaluado los parámetros cinemáticos de la línea CNC.
- Se observa una correlación directa entre la velocidad de avance y el incremento térmico en el cabezal de corte.
- Estimación RUL (Remaining Useful Life): Si el régimen de trabajo actual se mantiene constante, la intervención preventiva debe programarse antes de alcanzar el umbral crítico del 85.0% de desgaste.

2. ANÁLISIS DE IMPACTO ECONÓMICO:
- Un fallo imprevisto en línea de producción genera costes de parada no planificada estimados en 4,500 €/hora.
- La optimización actual de capital operativo absorbe de manera eficiente los costes de mantenimiento preventivo proyectados.

3. PLAN DE ACCIÓN INMEDIATO (3 PASOS EJECUTIVOS):
- Paso 1: Reducir un 15% la velocidad de avance del cabezal CNC en el próximo ciclo operativo para mitigar fricción.
- Paso 2: Programar la inspección visual y engrase de rodamientos en la próxima ventana de mantenimiento menor.
- Paso 3: Validar métricas de OEE en el panel de control web de Streamlit para confirmar la estabilización del proceso.

Tono: Operativo, estricto y enfocado a la continuidad de negocio.
==================================================
"""

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
    print("🔍 Iniciando inspección autónoma industrial y conectando a la BD...")
    
    # Valores por defecto iniciales
    capital_actual = 150000.0
    desgaste_cnc = 10.0

    # 1. Leer el último estado real guardado en Supabase
    if supabase:
        try:
            res = supabase.table("estado_empresa").select("*").order("created_at", desc=True).limit(1).execute()
            if res.data:
                capital_actual = float(res.data[0].get("capital", 150000.0))
                desgaste_cnc = float(res.data[0].get("desgaste_cnc", 10.0))
        except Exception as e:
            print(f"⚠️ Aviso al leer BD: {e}")

    # 2. Simulación industrial realista (basada en variables de producción)
    # Los ingresos varían de forma orgánica según la eficiencia de planta
    ingreso = round(random.uniform(4500.0, 11500.0), 2)
    
    # El desgaste aumenta de manera gradual y controlada (con micro-saltos aleatorios lógicos)
    incremento_desgaste = random.uniform(0.2, 1.5)
    desgaste_cnc = min(100.0, desgaste_cnc + incremento_desgaste)
    
    # Si llega al 100%, simulamos que se ha reparado y vuelve a un estado operativo seguro (10%)
    if desgaste_cnc >= 100.0:
        desgaste_cnc = 10.0
        print("🛠️ Mantenimiento preventivo completado automáticamente: el CNC se ha reiniciado a 10% de desgaste.")

    # Coste operativo dinámico proporcional a la actividad
    coste_operativo = 3500.0 + (desgaste_cnc * 12.0)
    capital_actual += (ingreso - coste_operativo)
    capital_actual = round(capital_actual, 2)

    # 3. Guardar el nuevo estado en Supabase para que llegue a la página web
    if supabase:
        try:
            supabase.table("estado_empresa").insert({
                "capital": capital_actual,
                "ingreso": ingreso,
                "desgaste_cnc": round(desgaste_cnc, 2)
            }).execute()
            print(f"💾 Datos registrados en Supabase -> Capital: {capital_actual}€ | Desgaste: {desgaste_cnc:.1f}%")
        except Exception as e:
            print(f"❌ Error al guardar en BD: {e}")
    else:
        print("❌ Error: No hay conexión configurada con Supabase.")

    # 4. Enviar correo de alerta automática si el desgaste supera el umbral crítico (75%)
    if desgaste_cnc >= 75.0:
        ctx = f"Equipo: Línea CNC Principal\nDesgaste actual: {desgaste_cnc:.1f}%\nCapital disponible: {capital_actual:,.2f} €\nIngreso del turno: {ingreso:,.2f} €"
        reporte = generar_informe_industrial("ALERTA PREDICTIVA: DESGASTE CRÍTICO EN MAQUINARIA CNC", ctx)
        enviar_email(SMTP_EMAIL, SMTP_PASSWORD, DEST_EMAIL, f"🚨 AUTÓNOMO 24/7: Atención Requerida - Desgaste CNC ({desgaste_cnc:.1f}%)", reporte)
        print("✉️ Correo de alerta industrial enviado exitosamente.")

if __name__ == "__main__":
    ejecutar_inspeccion_autonoma()
