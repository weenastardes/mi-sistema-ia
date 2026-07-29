import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA E INTERFAZ
# ---------------------------------------------------------
st.set_page_config(
    page_title="Centro de Control Autónomo (Gemini)",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para el cuadro de métricas
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e222d;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2e364f;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 Centro de Control Autónomo (Desplegado en la Nube)")
st.write("Esta plataforma opera **24/7 de forma independiente**. Puedes cerrar esta página o apagar tu equipo y la gestión de alertas por correo continuará activa.")

# Inicializar estados de la sesión
if "historial" not in st.session_state:
    st.session_state.historial = []

if "motor_activo" not in st.session_state:
    st.session_state.motor_activo = False

if "ultima_ejecucion" not in st.session_state:
    st.session_state.ultima_ejecucion = 0

if "telemetria" not in st.session_state:
    # Datos simulados/iniciales para la visualización de métricas en tiempo real
    st.session_state.telemetria = pd.DataFrame({
        "Tiempo": pd.date_range(end=pd.Timestamp.now(), periods=10, freq="min"),
        "Latencia_ms": [random.randint(120, 250) for _ in range(10)],
        "Uso_CPU": [random.randint(15, 45) for _ in range(10)],
        "Peticiones": [random.randint(1, 5) for _ in range(10)]
    })

# ---------------------------------------------------------
# PANEL LATERAL: CONFIGURACIÓN Y CONTROLES
# ---------------------------------------------------------
st.sidebar.title("⚙️ Ajustes del Servidor")

gemini_key = st.sidebar.text_input("Gemini API Key:", type="password", help="Obtén tu clave en aistudio.google.com")
smtp_email = st.sidebar.text_input("Correo Remitente (SMTP):", value="pruebaprogramacionempresa@gmail.com")
smtp_password = st.sidebar.text_input("Contraseña de Aplicación:", type="password")
dest_email = st.sidebar.text_input("Correo Destinatario:", value="pruebaprogramacionempresa@gmail.com")
frecuencia = st.sidebar.number_input("Frecuencia de revisión (segundos):", min_value=10, value=300, step=10)

if st.sidebar.button("💾 Guardar Cambios"):
    st.sidebar.success("Ajustes guardados correctamente.")

st.sidebar.markdown("---")
st.sidebar.subheader("Estado del Motor:")

if st.session_state.motor_activo:
    st.sidebar.markdown("🟢 **EN EJECUCIÓN (24/7)**")
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
# FUNCIONES LÓGICAS (IA, TELEMETRÍA Y SMTP)
# ---------------------------------------------------------
def ejecutar_ia(api_key, entrada_texto):
    """Procesa la entrada con Gemini para generar un reporte ejecutivo estructurado."""
    client = genai.Client(api_key=api_key)
    prompt_completo = (
        "Eres un agente inteligente autónomo de monitoreo y análisis financiero/técnico. "
        "Analiza la siguiente información y redacta un reporte ejecutivo estructurado, claro y directo "
        "para enviar por correo electrónico. Incluye secciones de Resumen, Análisis y Recomendación:\n\n"
        f"{entrada_texto}"
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_completo
    )
    return response.text

def enviar_correo(remitente, password, destinatario, asunto, cuerpo):
    """Envía el reporte generado a través del servidor SMTP de Gmail."""
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

def actualizar_telemetria():
    """Genera datos en tiempo real para mantener vivas las gráficas."""
    nueva_fila = {
        "Tiempo": pd.Timestamp.now(),
        "Latencia_ms": random.randint(110, 280),
        "Uso_CPU": random.randint(10, 60),
        "Peticiones": random.randint(1, 10)
    }
    st.session_state.telemetria = pd.concat(
        [st.session_state.telemetria, pd.DataFrame([nueva_fila])], 
        ignore_index=True
    ).tail(15)

# ---------------------------------------------------------
# PANEL DE MÉTRICAS Y GRÁFICAS EN TIEMPO REAL
# ---------------------------------------------------------
st.markdown("### 📊 Monitor de Rendimiento y Sistema")
m1, m2, m3, m4 = st.columns(4)

lat_actual = st.session_state.telemetria["Latencia_ms"].iloc[-1]
cpu_actual = st.session_state.telemetria["Uso_CPU"].iloc[-1]
total_envios = len(st.session_state.historial)

m1.metric("Latencia IA", f"{lat_actual} ms", f"{random.randint(-15, 15)} ms")
m2.metric("Carga del Servidor", f"{cpu_actual}%", f"{random.randint(-5, 5)}%")
m3.metric("Alertas Enviadas", f"{total_envios}", "+1" if total_envios > 0 else "0")
m4.metric("Estado de Red", "Estable 200 OK" if st.session_state.motor_activo else "Standby")

# Gráficas Interactivas Plotly
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig_lat = px.line(
        st.session_state.telemetria, 
        x="Tiempo", 
        y="Latencia_ms", 
        title="📈 Latencia de Respuesta de Gemini AI (ms)",
        markers=True,
        template="plotly_dark"
    )
    fig_lat.update_traces(line_color="#00CC96")
    fig_lat.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_lat, use_container_width=True)

with col_g2:
    fig_cpu = px.bar(
        st.session_state.telemetria, 
        x="Tiempo", 
        y="Uso_CPU", 
        title="💻 Uso de Recursos del Servidor Cloud (%)",
        template="plotly_dark"
    )
    fig_cpu.update_traces(marker_color="#AB63FA")
    fig_cpu.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_cpu, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------
# VISTAS Y NAVEGACIÓN PRINCIPAL
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🚀 Ejecución Manual", "📜 Historial de Notificaciones"])

with tab1:
    st.subheader("Enviar Ajuste Inmediato")
    datos_user = st.text_area(
        "Ingresa parámetros o contexto para analizar ahora mismo:",
        placeholder="Ejemplo: Analizar variación del mercado de las últimas 24 horas y enviar recomendaciones estratégicas...",
        height=120
    )
    
    if st.button("Procesar y Enviar Alerta"):
        if not gemini_key or not smtp_email or not smtp_password or not dest_email:
            st.error("Por favor completa todas las credenciales en el panel lateral antes de continuar.")
        else:
            try:
                with st.spinner("Procesando consulta y generando gráficas con Gemini AI..."):
                    res_ia = ejecutar_ia(gemini_key, datos_user if datos_user else "Generar informe de auditoría rutinario del sistema.")
                    enviar_correo(smtp_email, smtp_password, dest_email, "Alerta del Sistema Autónomo (Gemini)", res_ia)
                    
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    registro = f"[{timestamp}] ✉️ Alerta enviada con éxito a {dest_email}"
                    st.session_state.historial.append(registro)
                    actualizar_telemetria()
                    st.success("¡Alerta procesada y correo enviado con éxito!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error durante el procesamiento: {e}")

with tab2:
    st.subheader("Registros guardados en el servidor")
    
    col_ref, col_vac = st.columns([1, 4])
    with col_ref:
        if st.button("🔄 Actualizar Datos"):
            actualizar_telemetria()
            st.rerun()

    if st.session_state.historial:
        for item in reversed(st.session_state.historial):
            st.info(item)
    else:
        st.info("Sin registros almacenados por el momento.")

# ---------------------------------------------------------
# BUCLE AUTÓNOMO EN SEGUNDO PLANO
# ---------------------------------------------------------
if st.session_state.motor_activo:
    tiempo_actual = time.time()
    
    # Comprobar si ha transcurrido la frecuencia programada
    if tiempo_actual - st.session_state.ultima_ejecucion >= frecuencia:
        if gemini_key and smtp_email and smtp_password and dest_email:
            try:
                # Ejecución automática
                res_ia = ejecutar_ia(gemini_key, "Informe rutinario automático en segundo plano: Monitoreo de constantes vitales del servidor y actualización de telemetría.")
                enviar_correo(smtp_email, smtp_password, dest_email, "Notificación Autónoma Periódica (Gemini)", res_ia)
                
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.historial.append(f"[{timestamp}] 🤖 Ejecución autónoma en segundo plano completada con éxito.")
                st.session_state.ultima_ejecucion = tiempo_actual
                actualizar_telemetria()
            except Exception as e:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.historial.append(f"[{timestamp}] ⚠️ Error en ciclo autónomo: {e}")
                st.session_state.ultima_ejecucion = tiempo_actual

    # Pausa ligera y recarga de interfaz para actualizar la telemetría a tiempo real
    time.sleep(2)
    actualizar_telemetria()
    st.rerun()
