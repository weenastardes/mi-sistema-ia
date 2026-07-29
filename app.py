import os
import time
import sqlite3
import smtplib
import threading
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
import openai

# Configuración de registros
logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. BASE DE DATOS PERSISTENTE (SQLite)
# ==========================================
DB_FILE = "sistema_ia_cloud.db"

def init_db():
    """Inicializa la estructura de la base de datos."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY,
            openai_key TEXT,
            smtp_server TEXT,
            smtp_port INTEGER,
            email_remitente TEXT,
            email_password TEXT,
            email_destinatario TEXT,
            intervalo_segundos INTEGER,
            proceso_activo INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_ajustes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            datos_entrada TEXT,
            resultado_ajuste TEXT,
            correo_enviado INTEGER
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM configuracion")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO configuracion (id, openai_key, smtp_server, smtp_port, email_remitente, email_password, email_destinatario, intervalo_segundos, proceso_activo)
            VALUES (1, '', 'smtp.gmail.com', 465, '', '', '', 300, 0)
        """)
    
    conn.commit()
    conn.close()

def obtener_config():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT openai_key, smtp_server, smtp_port, email_remitente, email_password, email_destinatario, intervalo_segundos, proceso_activo FROM configuracion WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    return row

def guardar_config(openai_key, smtp_server, smtp_port, remitente, password, destinatario, intervalo, activo):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE configuracion 
        SET openai_key=?, smtp_server=?, smtp_port=?, email_remitente=?, email_password=?, email_destinatario=?, intervalo_segundos=?, proceso_activo=?
        WHERE id=1
    """, (openai_key, smtp_server, smtp_port, remitente, password, destinatario, intervalo, activo))
    conn.commit()
    conn.close()

def registrar_ajuste(fecha, entrada, salida, correo_enviado):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historial_ajustes (fecha, datos_entrada, resultado_ajuste, correo_enviado)
        VALUES (?, ?, ?, ?)
    """, (fecha, entrada, salida, 1 if correo_enviado else 0))
    conn.commit()
    conn.close()

def obtener_historial():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, datos_entrada, resultado_ajuste, correo_enviado FROM historial_ajustes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ==========================================
# 2. SERVICIO SMTP Y PROCESAMIENTO IA
# ==========================================
def generar_html_correo(timestamp, datos, resultado):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; }}
            .card {{ background-color: #ffffff; border-radius: 8px; padding: 25px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .header {{ color: #0d6efd; border-bottom: 2px solid #0d6efd; padding-bottom: 10px; }}
            .box {{ background: #f8f9fa; padding: 12px; border-left: 4px solid #0d6efd; margin: 15px 0; }}
            .box-success {{ background: #e8f5e9; border-left: 4px solid #2e7d32; padding: 12px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2 class="header">🤖 Notificación de Ajuste Automático</h2>
            <p><strong>Fecha/Hora:</strong> {timestamp}</p>
            <h3>📥 Parámetros Analizados:</h3>
            <div class="box"><p>{datos}</p></div>
            <h3>⚙️ Resultado del Ajuste por la IA:</h3>
            <div class="box-success"><p>{resultado.replace('\n', '<br>')}</p></div>
        </div>
    </body>
    </html>
    """

def enviar_correo(remitente, password, destinatario, servidor, puerto, asunto, cuerpo_html):
    mensaje = MIMEMultipart("alternative")
    mensaje['Subject'] = asunto
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    try:
        if int(puerto) == 465:
            with smtplib.SMTP_SSL(servidor, int(puerto), timeout=10) as server:
                server.login(remitente, password)
                server.sendmail(remitente, destinatario, mensaje.as_string())
        else:
            with smtplib.SMTP(servidor, int(puerto), timeout=10) as server:
                server.starttls()
                server.login(remitente, password)
                server.sendmail(remitente, destinatario, mensaje.as_string())
        return True
    except Exception as e:
        logging.error(f"Error al enviar correo: {e}")
        return False

def ejecutar_ia(api_key, datos):
    client = openai.OpenAI(api_key=api_key)
    system_prompt = (
        "Eres un motor de inteligencia artificial avanzado para gestión técnica y ajustes operativos. "
        "DEBES responder ÍNTEGRAMENTE EN ESPAÑOL. "
        "Estructura la respuesta de forma profesional con: Diagnóstico, Acciones Aplicadas y Recomendaciones."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Ajuste operativo requerido para:\n{datos}"}
        ]
    )
    return response.choices[0].message.content

# ==========================================
# 3. MOTOR AUTÓNOMO DE SEGUNDO PLANO
# ==========================================
def motor_de_fondo():
    """Ejecuta los análisis y correos en bucle sin importar la interfaz."""
    logging.info("Motor en segundo plano iniciado...")
    while True:
        try:
            cfg = obtener_config()
            openai_key, smtp_server, smtp_port, remitente, password, destinatario, intervalo, activo = cfg

            if activo == 1 and openai_key and remitente and password and destinatario:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                datos_monitoreo = f"Revisión automática de estado del sistema — {timestamp}"
                
                # Procesamiento con la IA
                resultado = ejecutar_ia(openai_key, datos_monitoreo)
                html = generar_html_correo(timestamp, datos_monitoreo, resultado)
                
                # Envío de correo
                exito = enviar_correo(remitente, password, destinatario, smtp_server, smtp_port, f"⚡ [Sistema IA] Reporte Automático - {timestamp}", html)
                
                # Registro en base de datos
                registrar_ajuste(timestamp, datos_monitoreo, resultado, exito)

            time.sleep(max(15, intervalo))
        except Exception as e:
            logging.error(f"Error en hilo autónomo: {e}")
            time.sleep(15)

# Inicializar Base de Datos y arrancar el motor de fondo
init_db()
if not any(thread.name == "WorkerCloudThread" for thread in threading.enumerate()):
    t = threading.Thread(target=motor_de_fondo, name="WorkerCloudThread", daemon=True)
    t.start()

# ==========================================
# 4. INTERFAZ VISUAL WEB (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Panel de Control IA 24/7", page_icon="🌐", layout="wide")

cfg = obtener_config()
st_key, st_server, st_port, st_remitente, st_password, st_destinatario, st_intervalo, st_activo = cfg

st.title("🌐 Centro de Control Autónomo (Desplegado en la Nube)")
st.markdown("Esta plataforma opera **24/7 de forma independiente**. Puedes cerrar esta página o apagar tu equipo y la gestión de alertas por correo continuará activa.")
st.markdown("---")

# Barra lateral para credenciales y parámetros
st.sidebar.title("⚙️ Ajustes del Servidor")
with st.sidebar.form("config_cloud"):
    input_key = st.text_input("OpenAI API Key:", value=st_key, type="password")
    input_remitente = st.text_input("Correo Remitente (SMTP):", value=st_remitente)
    input_password = st.text_input("Contraseña de Aplicación:", value=st_password, type="password")
    input_destinatario = st.text_input("Correo Destinatario:", value=st_destinatario)
    input_intervalo = st.number_input("Frecuencia de revisión (segundos):", min_value=15, value=st_intervalo)
    
    btn_guardar = st.form_submit_button("💾 Guardar Cambios")

if btn_guardar:
    guardar_config(input_key, st_server, st_port, input_remitente, input_password, input_destinatario, input_intervalo, st_activo)
    st.sidebar.success("Configuración actualizada.")
    st.rerun()

st.sidebar.markdown("---")
estado_texto = "🟢 EN EJECUCIÓN (24/7)" if st_activo == 1 else "🔴 DETENIDO"
st.sidebar.markdown(f"**Estado del Motor:** `{estado_texto}`")

c1, c2 = st.sidebar.columns(2)
if c1.button("▶️ Activar"):
    guardar_config(st_key, st_server, st_port, st_remitente, st_password, st_destinatario, st_intervalo, 1)
    st.rerun()

if c2.button("⏹️ Apagar"):
    guardar_config(st_key, st_server, st_port, st_remitente, st_password, st_destinatario, st_intervalo, 0)
    st.rerun()

# Pestañas de gestión
tab_manual, tab_historial = st.tabs(["🚀 Ejecución Manual", "📜 Historial de Notificaciones"])

with tab_manual:
    st.subheader("Enviar Ajuste Inmediato")
    datos_user = st.text_area("Ingresa parámetros para analizar ahora mismo:", height=150)
    if st.button("Procesar y Enviar Alerta"):
        if not datos_user.strip():
            st.warning("Escribe los datos de entrada.")
        elif not st_key or not st_remitente or not st_password:
            st.error("Completa la configuración en la barra lateral antes de continuar.")
        else:
            with st.spinner("Procesando consulta con la IA..."):
                res = ejecutar_ia(st_key, datos_user)
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                html = generar_html_correo(ts, datos_user, res)
                exito = enviar_correo(st_remitente, st_password, st_destinatario, st_server, st_port, f"📌 [Ajuste Manual] - {ts}", html)
                registrar_ajuste(ts, datos_user, res, exito)
                
                if exito:
                    st.success(f"Ajuste completado y correo enviado a {st_destinatario}")
                else:
                    st.warning("El ajuste se calculó pero falló el envío del correo.")
                st.info(res)

with tab_historial:
    st.subheader("Registros guardados en el servidor")
    if st.button("🔄 Actualizar Datos"):
        st.rerun()
        
    historial = obtener_historial()
    if not historial:
        st.info("Sin registros almacenados.")
    else:
        for fch, ent, sal, cor in historial:
            with st.expander(f"📅 {fch} — Notificado: {'✅ Sí' if cor == 1 else '❌ No'}"):
                st.write(f"**Entrada:** {ent}")
                st.markdown(f"**Resultado:**\n{sal}")