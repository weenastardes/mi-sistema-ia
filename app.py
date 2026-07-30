import streamlit as st
import pandas as pd
import numpy as np
import random
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from supabase import create_client

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS DE LA INTERFAZ
# ---------------------------------------------------------
st.set_page_config(
    page_title="ERP Industrial & Monitor Predictivo IA 24/7",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado mediante CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    .status-ok {
        color: #22c55e;
        font-weight: bold;
    }
    .status-alert {
        color: #ef4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. LECTURA DE SECRETOS Y ENTORNO
# ---------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "pruebaprogramacionempresa@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD") or st.secrets.get("SMTP_PASSWORD")
DEST_EMAIL = os.environ.get("DEST_EMAIL", "pruebaprogramacionempresa@gmail.com")

# ---------------------------------------------------------
# 3. CONEXIÓN A BASE DE DATOS (SUPABASE)
# ---------------------------------------------------------
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.sidebar.error(f"Error conectando a Supabase: {e}")

def cargar_datos_bd():
    """Consulta la tabla estado_empresa en Supabase y devuelve un DataFrame ordenado."""
    if supabase:
        try:
            res = supabase.table("estado_empresa").select("*").order("created_at", desc=False).execute()
            if res.data:
                df = pd.DataFrame(res.data)
                if 'created_at' in df.columns:
                    df['created_at'] = pd.to_datetime(df['created_at'])
                return df
        except Exception as e:
            st.sidebar.warning(f"Error al cargar datos desde la BD: {e}")
    return pd.DataFrame()

def guardar_estado_bd(capital, ingreso, desgaste):
    """Inserta una nueva lectura realizada manualmente desde la web."""
    if supabase:
        try:
            supabase.table("estado_empresa").insert({
                "capital": capital,
                "ingreso": ingreso,
                "desgaste_cnc": desgaste
            }).execute()
            return True
        except Exception as e:
            st.error(f"Error al guardar datos en Supabase: {e}")
    return False

# ---------------------------------------------------------
# 4. FUNCIONES DE IA (GEMINI) Y NOTIFICACIONES (SMTP)
# ---------------------------------------------------------
def consultar_gemini(api_key, tipo_evento, contexto):
    """Consulta al modelo de Inteligencia Artificial para generar informes predictivos."""
    if not api_key:
        return "⚠️ Error: Clave de API de Gemini no detectada. Configúrala en los secretos."
    
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Eres el Director Técnico e Inteligencia Artificial Supervisora de la planta Industrias Innovación S.L.
    
    TIPO DE INCIDENCIA DETECTADA: {tipo_evento}
    DATOS OPERATIVOS EN TIEMPO REAL:
    {contexto}

    REQUERIMIENTOS ESTRUCTURADOS DEL INFORME:
    1. DIAGNÓSTICO PREDICTIVO: Evaluación de vida útil restante del equipo (RUL).
    2. ANÁLISIS DE IMPACTO ECONÓMICO: Riesgo potencial en ingresos y costes de parada.
    3. PLAN DE ACCIÓN EJECUTIVO: 3 medidas correctivas inmediatas a tomar por el equipo técnico.
    4. CONCLUSIÓN FINAL Y RECOMENDACIÓN OPERATIVA.
    
    Asegúrate de mantener un tono directivo, técnico, profesional y de urgencia.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error consultando el motor Gemini: {e}"

def enviar_email(remitente, password, destinatario, asunto, cuerpo):
    """Envía correos electrónicos automáticos vía SMTP."""
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
        return True
    except Exception as e:
        st.error(f"Error al enviar la alerta por correo: {e}")
        return False

# ---------------------------------------------------------
# 5. CARGA INICIAL Y ESTADO DE SESIÓN
# ---------------------------------------------------------
df_historico = cargar_datos_bd()

if not df_historico.empty:
    st.session_state.capital = float(df_historico.iloc[-1]['capital'])
    st.session_state.desgaste_cnc = float(df_historico.iloc[-1]['desgaste_cnc'])
    st.session_state.ultimo_ingreso = float(df_historico.iloc[-1].get('ingreso', 8000.0))
else:
    if 'capital' not in st.session_state:
        st.session_state.capital = 150000.0
    if 'desgaste_cnc' not in st.session_state:
        st.session_state.desgaste_cnc = 10.0
    if 'ultimo_ingreso' not in st.session_state:
        st.session_state.ultimo_ingreso = 8000.0

# ---------------------------------------------------------
# 6. BARRA LATERAL DE NAVEGACIÓN Y CONFIGURACIÓN
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/factory.png", width=70)
st.sidebar.title("Navegación ERP")
st.sidebar.markdown("---")

opcion_menu = st.sidebar.radio(
    "Selecciona un Módulo:",
    ["📊 Dashboard Control 24/7", "🧪 Centro de Simulación", "📜 Registros Base de Datos", "🤖 Módulo IA Supervisor", "⚙️ Configuración & API"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Estado de Infraestructura")
if supabase:
    st.sidebar.success("Base de Datos: Conectada")
else:
    st.sidebar.warning("Base de Datos: Modo Local")

if GEMINI_API_KEY:
    st.sidebar.success("Gemini AI: Activo")
else:
    st.sidebar.error("Gemini AI: Inactivo")

if SMTP_PASSWORD:
    st.sidebar.success("Servidor SMTP: Activo")
else:
    st.sidebar.error("Servidor SMTP: Inactivo")

# ---------------------------------------------------------
# 7. CABECERA PRINCIPAL
# ---------------------------------------------------------
st.title("🏭 ERP Industrial & Monitor Predictivo IA 24/7")
st.caption("Sistema Avanzado de Gestión de Planta, Métricas Financieras y Supervisión Predictiva en la Nube")
st.markdown("---")

# ---------------------------------------------------------
# MÓDULO 1: DASHBOARD PRINCIPAL
# ---------------------------------------------------------
if opcion_menu == "📊 Dashboard Control 24/7":
    
    # Fila de Métricas Clave (KPIs)
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    kpi1.metric("Capital Operativo", f"{st.session_state.capital:,.2f} €", delta=f"{st.session_state.ultimo_ingreso - 4000:.2f} €")
    kpi2.metric("Desgaste CNC", f"{st.session_state.desgaste_cnc:.1f} %", delta="Salud Maquinaria", delta_color="inverse")
    
    # Cálculo de métricas ERP derivadas
    oee_estimado = max(0.0, 100.0 - (st.session_state.desgaste_cnc * 0.6))
    kpi3.metric("OEE de Planta", f"{oee_estimado:.1f} %")
    
    margin = ((st.session_state.ultimo_ingreso - 4000) / max(st.session_state.ultimo_ingreso, 1)) * 100
    kpi4.metric("Margen del Turno", f"{margin:.1f} %")
    
    if st.session_state.desgaste_cnc >= 75.0:
        kpi5.metric("Nivel de Riesgo", "🚨 CRÍTICO", delta="Mantenimiento Requerido", delta_color="inverse")
    else:
        kpi5.metric("Nivel de Riesgo", "✅ NOMINAL", delta="Sin anomalías")

    st.markdown("---")

    # Gráficas Principales
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("📉 Historia de Capital Operativo (€)")
        if not df_historico.empty and "capital" in df_historico.columns:
            st.line_chart(df_historico.set_index("created_at")["capital"] if "created_at" in df_historico.columns else df_historico["capital"])
        else:
            st.info("Aún no hay suficientes registros en la base de datos para mostrar la tendencia.")

    with col_g2:
        st.subheader("⚙️ Evolución del Desgaste de Maquinaria (%)")
        desgaste_pct = int(min(st.session_state.desgaste_cnc, 100))
        st.progress(desgaste_pct)
        
        if not df_historico.empty and "desgaste_cnc" in df_historico.columns:
            st.area_chart(df_historico["desgaste_cnc"])
        else:
            st.info("Genera turnos o espera a las lecturas autónomas de GitHub para ver la gráfica de desgaste.")

    st.markdown("---")
    
    # Sección de Diagnóstico Rápido
    st.subheader("📋 Resumen Ejecutivo de la Planta")
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.write("**Línea Principales de Producción:** CNC Láser 5-Axis")
        st.write("**Ubicación:** Nave Industrial Sector A4")
        st.write("**Estado de Conectividad:** Servidores GitHub Actions vinculados 24/7 cada 5 min")
    
    with res_col2:
        if st.session_state.desgaste_cnc >= 75.0:
            st.error("🚨 La maquinaria ha alcanzado el umbral de parada preventiva. Se recomienda solicitar auditoría con la IA en la pestaña 'Módulo IA Supervisor'.")
        else:
            st.success("✅ Todos los sistemas funcionan dentro de los parámetros de tolerancia.")

# ---------------------------------------------------------
# MÓDULO 2: CENTRO DE SIMULACIÓN Y MANTENIMIENTO
# ---------------------------------------------------------
elif opcion_menu == "🧪 Centro de Simulación":
    st.subheader("⚡ Simulador Manual de Eventos y Mantenimiento")
    st.write("Usa esta pestaña para forzar pruebas financieras, simular desgaste acelerado o ejecutar mantenimientos que restauren el estado de la planta.")

    sim_col1, sim_col2 = st.columns(2)

    with sim_col1:
        st.markdown("### 🎲 Simular Turno de Trabajo")
        ingreso_sim = st.number_input("Ingresos netos por entregas (€)", value=8000, step=1000)
        desgaste_sim = st.slider("Incremento de desgaste en este turno (%)", 0.0, 30.0, 3.5)
        
        if st.button("🚀 Ejecutar Turno de Producción"):
            st.session_state.capital += (ingreso_sim - 4000.0)
            st.session_state.desgaste_cnc = min(100.0, st.session_state.desgaste_cnc + desgaste_sim)
            st.session_state.ultimo_ingreso = ingreso_sim
            
            guardar_estado_bd(st.session_state.capital, ingreso_sim, st.session_state.desgaste_cnc)
            st.success(f"Turno procesado. Capital actualizado: {st.session_state.capital:,.2f} €")
            
            if st.session_state.desgaste_cnc >= 75.0:
                st.error("🚨 Se ha superado el umbral del 75% de desgaste.")
                if SMTP_PASSWORD:
                    ctx = f"Desgaste actual: {st.session_state.desgaste_cnc:.1f}%\nCapital: {st.session_state.capital:,.2f} €"
                    reporte = consultar_gemini(GEMINI_API_KEY, "ALERTA WEB MANUALLY TRIGGERED", ctx)
                    enviar_email(SMTP_EMAIL, SMTP_PASSWORD, DEST_EMAIL, f"🚨 ALERTA WEB: Desgaste al {st.session_state.desgaste_cnc:.1f}%", reporte)
                    st.info("Correo de notificación enviado con éxito.")
            st.rerun()

    with sim_col2:
        st.markdown("### 🛠️ Mantenimiento Técnico de Planta")
        st.write("Si el desgaste es elevado, puedes invertir capital operativo para realizar una revisión técnica y poner la maquinaria a punto.")
        
        coste_mantenimiento = 12000.0
        st.write(f"**Coste de Mantenimiento Preventivo:** {coste_mantenimiento:,.2f} €")
        
        if st.button("🔧 Ejecutar Mantenimiento Completo"):
            if st.session_state.capital >= coste_mantenimiento:
                st.session_state.capital -= coste_mantenimiento
                st.session_state.desgaste_cnc = 5.0
                guardar_estado_bd(st.session_state.capital, 0, st.session_state.desgaste_cnc)
                st.balloons()
                st.success("Mantenimiento realizado con éxito. Maquinaria calibrada al 5.0% de desgaste.")
                st.rerun()
            else:
                st.error("Capital insuficiente para costear el mantenimiento.")

# ---------------------------------------------------------
# MÓDULO 3: REGISTROS Y BASE DE DATOS DETALLADA
# ---------------------------------------------------------
elif opcion_menu == "📜 Registros Base de Datos":
    st.subheader("📜 Consulta e Histórico Completo de Supabase")
    st.write("Aquí se listan todas las entradas guardadas tanto por el servicio de automatización de GitHub Actions como por los turnos simularos manualmente.")

    if st.button("🔄 Refrescar Datos desde Supabase"):
        st.rerun()

    df_bd = cargar_datos_bd()
    
    if not df_bd.empty:
        # Filtros para la tabla
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            registros_mostrar = st.slider("Número de registros a mostrar:", 5, 100, 20)
        
        st.dataframe(df_bd.tail(registros_mostrar), use_container_width=True)
        
        # Opción de Descarga
        csv = df_bd.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Histórico como CSV",
            data=csv,
            file_name=f"historico_erp_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay datos en la base de datos actualmente. Asegúrate de ejecutar el workflow en GitHub o generar turnos en el simulador.")

# ---------------------------------------------------------
# MÓDULO 4: IA SUPERVISOR (GEMINI CHAT & INFORME)
# ---------------------------------------------------------
elif opcion_menu == "🤖 Módulo IA Supervisor":
    st.subheader("🤖 Consultoría Técnica Predictiva con Gemini AI")
    st.write("Genera dictámenes personalizados sobre la condición de la planta usando Inteligencia Artificial.")

    col_ia1, col_ia2 = st.columns([1, 2])

    with col_ia1:
        st.markdown("### Parámetros de Inspección")
        tipo_auditoria = st.selectbox(
            "Selecciona el tipo de auditoría:",
            ["Auditoría General Preventiva", "Evaluación de Riesgo de Parada", "Optimización de Costes y Financiera"]
        )
        
        btn_generar = st.button("🔍 Solicitar Dictamen a Gemini")

    with col_ia2:
        if btn_generar:
            with st.spinner("Analizando parámetros de planta y redactando informe..."):
                ctx = f"""
                - Capital Operativo Disponible: {st.session_state.capital:,.2f} €
                - Desgaste Acumulado Maquinaria CNC: {st.session_state.desgaste_cnc:.1f} %
                - Ingreso del último ciclo: {st.session_state.ultimo_ingreso:,.2f} €
                - Estado Conexión Nube: Activa (Supabase)
                """
                informe_generado = consultar_gemini(GEMINI_API_KEY, tipo_auditoria, ctx)
                st.markdown("### 📋 Informe Predictivo Emitido:")
                st.info(informe_generado)

# ---------------------------------------------------------
# MÓDULO 5: CONFIGURACIÓN Y ESTADO DE CREDENCIALES
# ---------------------------------------------------------
elif opcion_menu == "⚙️ Configuración & API":
    st.subheader("⚙️ Estado de la Configuración y Variables de Entorno")
    st.write("Verifica el estado de conexión de tus variables de entorno clave.")

    st.markdown("---")
    st.markdown("### 🔑 Lista de Variables Detectadas")
    
    cfg1, cfg2 = st.columns(2)
    
    with cfg1:
        st.write("**SUPABASE_URL:**", "`" + (SUPABASE_URL[:20] + "..." if SUPABASE_URL else "No configurado") + "`")
        st.write("**SUPABASE_KEY:**", "`" + (SUPABASE_KEY[:10] + "..." if SUPABASE_KEY else "No configurado") + "`")
        st.write("**GEMINI_API_KEY:**", "`" + (GEMINI_API_KEY[:10] + "..." if GEMINI_API_KEY else "No configurado") + "`")

    with cfg2:
        st.write("**SMTP_EMAIL (Remitente):**", f"`{SMTP_EMAIL}`")
        st.write("**SMTP_PASSWORD:**", "`" + ("********" if SMTP_PASSWORD else "No configurado") + "`")
        st.write("**DEST_EMAIL (Destinatario):**", f"`{DEST_EMAIL}`")

    st.markdown("---")
    st.markdown("### 🧪 Prueba Manual del Servidor SMTP")
    if st.button("📧 Enviar Correo de Prueba"):
        if SMTP_PASSWORD:
            exito = enviar_email(
                SMTP_EMAIL, 
                SMTP_PASSWORD, 
                DEST_EMAIL, 
                "🧪 Prueba de Sistema ERP", 
                "Este es un correo de verificación enviado desde la interfaz de Streamlit."
            )
            if exito:
                st.success("¡Correo de prueba enviado con éxito!")
        else:
            st.error("No se puede enviar la prueba porque falta la contraseña SMTP_PASSWORD.")
