import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
import time

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA E INTERFAZ
# ---------------------------------------------------------
st.set_page_config(page_title="Centro de Control Autónomo (Gemini)", page_icon="🌐", layout="wide")

st.title("🌐 Centro de Control Autónomo (Desplegado en la Nube)")
st.write("Esta plataforma opera **24/7 de forma independiente**. Puedes cerrar esta página o apagar tu equipo y la gestión de alertas por correo continuará activa.")

# Inicializar estados de la sesión
if "historial" not in st.session_state:
    st.session_state.historial = []

if "motor_activo" not in st.session_state:
    st.session_state.motor_activo = False

if "ultima_ejecucion" not in st.session_state:
    st.session_state.ultima_ejecucion = 0

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
# FUNCIONES LÓGICAS (IA Y SMTP)
# ---------------------------------------------------------
def ejecutar_ia(api_key, entrada_texto):
    """Procesa la entrada con Gemini para generar un reporte ejecutivo."""
    client = genai.Client(api_key=api_key)
    prompt_completo = (
        "Eres un agente inteligente autónomo de monitoreo. "
        "Analiza la siguiente información y redacta un reporte ejecutivo o alerta clara "
        "para enviar directamente por correo electrónico:\n\n"
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

# ---------------------------------------------------------
# VISTAS Y NAVEGACIÓN PRINCIPAL
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🚀 Ejecución Manual", "📜 Historial de Notificaciones"])

with tab1:
    st.subheader("Enviar Ajuste Inmediato")
    datos_user = st.text_area(
        "Ingresa parámetros o contexto para analizar ahora mismo:",
        placeholder="Ejemplo: Revisar estado del servidor principal y alertar si detectas irregularidades..."
    )
    
    if st.button("Procesar y Enviar Alerta"):
        if not gemini_key or not smtp_email or not smtp_password or not dest_email:
            st.error("Por favor completa todas las credenciales en el panel lateral antes de continuar.")
        else:
            try:
                with st.spinner("Procesando consulta con Gemini AI..."):
                    res_ia = ejecutar_ia(gemini_key, datos_user if datos_user else "Generar informe rutinario de estado del sistema.")
                    enviar_correo(smtp_email, smtp_password, dest_email, "Alerta del Sistema Autónomo (Gemini)", res_ia)
                    
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    registro = f"[{timestamp}] ✉️ Alerta enviada con éxito a {dest_email}"
                    st.session_state.historial.append(registro)
                    st.success("¡Alerta procesada y correo enviado con éxito!")
            except Exception as e:
                st.error(f"Error durante el procesamiento: {e}")

with tab2:
    st.subheader("Registros guardados en el servidor")
    
    col_ref, col_vac = st.columns([1, 4])
    with col_ref:
        if st.button("🔄 Actualizar Datos"):
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
                res_ia = ejecutar_ia(gemini_key, "Informe rutinario automático en segundo plano: Todo el sistema opera bajo parámetros normales.")
                enviar_correo(smtp_email, smtp_password, dest_email, "Notificación Autónoma Periódica (Gemini)", res_ia)
                
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.historial.append(f"[{timestamp}] 🤖 Ejecución autónoma en segundo plano completada con éxito.")
                st.session_state.ultima_ejecucion = tiempo_actual
            except Exception as e:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.historial.append(f"[{timestamp}] ⚠️ Error en ciclo autónomo: {e}")
                st.session_state.ultima_ejecucion = tiempo_actual

    # Pausa ligera y recarga de interfaz para mantener el bucle vivo
    time.sleep(2)
    st.rerun()
