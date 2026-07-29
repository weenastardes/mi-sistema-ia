import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistema Autónomo de Predictiva y Gestión",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Sistema Autónomo de Gestión Empresarial y Alerta de Picos")
st.write("El sistema monitorea métricas empresariales clave en tiempo real, genera **predicciones automáticas** y solo **envía alertas al correo cuando detecta anomalías o picos bruscos**.")

# Inicializar estados
if "historial" not in st.session_state:
    st.session_state.historial = []

if "motor_activo" not in st.session_state:
    st.session_state.motor_activo = False

if "ultima_ejecucion" not in st.session_state:
    st.session_state.ultima_ejecucion = 0

# Generador de datos empresariales (Ventas / Demanda / Métricas de Negocio)
if "datos_empresa" not in st.session_state:
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=20, freq="15min")
    # Simulación de métrica empresarial base (ej. Ventas/minuto o Tráfico)
    valores_base = [random.randint(800, 1200) for _ in range(20)]
    st.session_state.datos_empresa = pd.DataFrame({
        "Tiempo": fechas,
        "Metrica_Negocio": valores_base
    })

# ---------------------------------------------------------
# PANEL LATERAL
# ---------------------------------------------------------
st.sidebar.title("⚙️ Configuración del Agente")

gemini_key = st.sidebar.text_input("Gemini API Key:", type="password", help="Obtén tu clave en aistudio.google.com")
smtp_email = st.sidebar.text_input("Correo Remitente (SMTP):", value="pruebaprogramacionempresa@gmail.com")
smtp_password = st.sidebar.text_input("Contraseña de Aplicación:", type="password")
dest_email = st.sidebar.text_input("Correo Destinatario:", value="pruebaprogramacionempresa@gmail.com")

st.sidebar.markdown("---")
st.sidebar.subheader("🎚️ Umbral de Sensibilidad para Alertas")
umbral_sensibilidad = st.sidebar.slider("Sensibilidad para detectar picos (% de desviación):", 15, 60, 30)
frecuencia = st.sidebar.number_input("Frecuencia de monitoreo (segundos):", min_value=10, value=60, step=10)

st.sidebar.markdown("---")
st.sidebar.subheader("Estado del Motor:")

if st.session_state.motor_activo:
    st.sidebar.markdown("🟢 **MONITOREO ACTIVO (24/7)**")
else:
    st.sidebar.markdown("🔴 **DETENIDO**")

col_act, col_apa = st.sidebar.columns(2)
with col_act:
    if st.button("▶️ Activar"):
        st.session_state.motor_activo = True
        st.rerun()

with col_apa:
    if st.button("⏹️ Apagar"):
        st.session_state.motor_activo = False
        st.rerun()

# ---------------------------------------------------------
# LÓGICA DE DETECCIÓN, PREDICCIÓN E IA
# ---------------------------------------------------------
def analizar_y_predecir_con_gemini(api_key, df, pico_detectado, porcentaje_desviacion):
    """Llama a Gemini 2.0 Flash para analizar la causa del pico y predecir tendencias."""
    client = genai.Client(api_key=api_key)
    
    ultimos_datos = df.tail(10).to_string()
    
    prompt = f"""
    Eres el Director de Operaciones e IA de una empresa.
    Se ha detectado una ANOMALÍA / PICO BRUSCO en las métricas del negocio.

    DATOS RECIENTES DEL NEGOCIO:
    {ultimos_datos}

    DETALLES DE LA ANOMALÍA:
    - Desviación detectada respecto al promedio: {porcentaje_desviacion:.2f}%
    - ¿Se considera un pico crítico?: {pico_detectado}

    INSTRUCCIONES:
    1. Realiza una PREDICCIÓN de lo que pasará en las próximas 2 horas si esto no se atiende.
    2. Proporciona 3 ACCIONES INMEDIATAS de gestión empresarial que la directiva debe tomar.
    3. Redacta el mensaje en formato de Alerta Ejecutiva Urgente.
    """
    
    # Modelo oficial y activo de Google Gemini
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

def enviar_correo(remitente, password, destinatario, asunto, cuerpo):
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

def simular_nuevo_dato_y_evaluar(forzar_pico=False):
    """Agrega un nuevo dato al histórico y verifica si hay un pico brusco."""
    df = st.session_state.datos_empresa
    media = df["Metrica_Negocio"].mean()
    
    if forzar_pico:
        # Genera un pico brusco intencional (ej. caída masiva o subida repentina)
        nuevo_valor = int(media * random.choice([1.7, 0.3]))
    else:
        nuevo_valor = int(random.gauss(media, 80))

    nueva_fila = {
        "Tiempo": pd.Timestamp.now(),
        "Metrica_Negocio": nuevo_valor
    }
    
    st.session_state.datos_empresa = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True).tail(25)
    
    # Evaluar si la variación supera el umbral de sensibilidad
    desviacion = abs(nuevo_valor - media) / media * 100
    es_pico = desviacion >= umbral_sensibilidad
    
    return nuevo_valor, media, desviacion, es_pico

# ---------------------------------------------------------
# CUADRO DE MANDO EMPRESARIAL
# ---------------------------------------------------------
df_actual = st.session_state.datos_empresa
ultimo_valor = df_actual["Metrica_Negocio"].iloc[-1]
media_historica = df_actual["Metrica_Negocio"].mean()
desviacion_actual = abs(ultimo_valor - media_historica) / media_historica * 100
hay_pico = desviacion_actual >= umbral_sensibilidad

m1, m2, m3, m4 = st.columns(4)
m1.metric("Métrica de Negocio (Actual)", f"{ultimo_valor} uds")
m2.metric("Promedio Histórico", f"{int(media_historica)} uds")
m3.metric("Desviación Detectada", f"{desviacion_actual:.1f}%", delta_color="inverse")

if hay_pico:
    m4.error("🚨 PICO BRUSCO DETECTADO")
else:
    m4.success("🟢 Parámetros Normales")

# Gráfica de Negocio con Indicador de Anomalía
fig = px.line(
    df_actual, 
    x="Tiempo", 
    y="Metrica_Negocio", 
    title="📊 Monitoreo de Operaciones Empresariales en Tiempo Real",
    markers=True,
    template="plotly_dark"
)

# Dibujar línea del promedio y zona de umbral
fig.add_hline(y=media_historica, line_dash="dash", line_color="yellow", annotation_text="Promedio")

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# ACCIONES MANUALES DE GESTIÓN Y SIMULACIÓN DE PICOS
# ---------------------------------------------------------
st.markdown("---")
c1, c2 = st.columns(2)

with c1:
    st.subheader("🧪 Probar Gestión Autónoma de Picos")
    st.write("Haz clic aquí para **simular un pico brusco en el negocio**. La IA analizará la desviación, creará una predicción y **te mandará el correo de alerta automáticamente**.")
    
    if st.button("⚠️ Simular Pico Brusco en la Empresa"):
        if not gemini_key or not smtp_email or not smtp_password or not dest_email:
            st.error("Rellena las credenciales en la barra lateral primero.")
        else:
            val, med, des, es_pico = simular_nuevo_dato_y_evaluar(forzar_pico=True)
            with st.spinner("Pico detectado. La IA de Gemini está analizando el impacto empresarial y enviando el correo..."):
                try:
                    informe_ia = analizar_y_predecir_con_gemini(gemini_key, st.session_state.datos_empresa, es_pico, des)
                    enviar_correo(
                        smtp_email, 
                        smtp_password, 
                        dest_email, 
                        f"🚨 ALERTA EMPRESARIAL: Pico Brusco Detectado ({des:.1f}% Desviación)", 
                        informe_ia
                    )
                    
                    t_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    st.session_state.historial.append(f"[{t_stamp}] 🚨 Pico del {des:.1f}% detectado. Alerta con predicciones enviada a {dest_email}")
                    st.success("¡Anomalía procesada! Se ha enviado la predicción y el plan de gestión a tu correo.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error procesando con la IA: {e}")

with c2:
    st.subheader("📜 Registro de Alertas de Gestión Enviadas")
    if st.session_state.historial:
        for reg in reversed(st.session_state.historial):
            st.warning(reg)
    else:
        st.info("No se han enviado correos aún. El sistema solo enviará alertas cuando la IA detecte un pico significativo.")

# ---------------------------------------------------------
# BUCLE AUTOMÁTICO EN SEGUNDO PLANO
# ---------------------------------------------------------
if st.session_state.motor_activo:
    tiempo_act = time.time()
    if tiempo_act - st.session_state.ultima_ejecucion >= frecuencia:
        val, med, des, es_pico = simular_nuevo_dato_y_evaluar(forzar_pico=False)
        st.session_state.ultima_ejecucion = tiempo_act
        
        # SOLO SI HAY UN PICO BRUSCO SE EJECUTA LA IA Y ENVÍA EL CORREO
        if es_pico and gemini_key and smtp_email and smtp_password and dest_email:
            try:
                informe_ia = analizar_y_predecir_con_gemini(gemini_key, st.session_state.datos_empresa, es_pico, des)
                enviar_correo(
                    smtp_email, 
                    smtp_password, 
                    dest_email, 
                    f"🚨 AUTÓNOMO: Desviación Brusca Detectada en el Negocio ({des:.1f}%)", 
                    informe_ia
                )
                t_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.historial.append(f"[{t_stamp}] 🤖 ALERTA AUTOMÁTICA: Pico detectado y notificado por correo.")
            except Exception as e:
                t_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.historial.append(f"[{t_stamp}] ⚠️ Error en ciclo autónomo: {e}")
                
        st.rerun()

    time.sleep(2)
    st.rerun()
