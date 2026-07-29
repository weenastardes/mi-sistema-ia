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
    page_title="Plataforma de Mantenimiento Predictivo & IA Financiera",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales personalizados
st.markdown("""
    <style>
    .metric-box {
        background-color: #1e222d;
        border-left: 5px solid #00E676;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .alert-box {
        background-color: #2d1e1e;
        border-left: 5px solid #FF5252;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 ERP Predictivo & Agente Autónomo de Operaciones")
st.caption("Sistema de monitoreo continuo, detección de anomalías en maquinaria y auditoría financiera inteligente para PYMES e Industrias.")

# ---------------------------------------------------------
# INICIALIZACIÓN DE ESTADOS PERSISTENTES
# ---------------------------------------------------------
if "empresa_nombre" not in st.session_state:
    st.session_state.empresa_nombre = "Industrias Innovación S.L."

if "capital" not in st.session_state:
    st.session_state.capital = 150000.0

if "costos_fijos" not in st.session_state:
    st.session_state.costos_fijos = {
        "Nóminas Plantilla": 18500.0,
        "Alquiler Nave Industrial": 3500.0,
        "Electricidad y Agua": 2800.0,
        "Licencias y Seguros": 1200.0
    }

if "maquinaria" not in st.session_state:
    st.session_state.maquinaria = {
        "Prensa Hidráulica H-500": {"desgaste": 22.0, "temp_c": 65.0, "vibracion_hz": 12.0, "horas": 450, "costo_reparacion": 2500.0, "costo_fallo_catastrofico": 18000.0},
        "Línea de Corte Láser CNC": {"desgaste": 48.0, "temp_c": 72.0, "vibracion_hz": 18.0, "horas": 890, "costo_reparacion": 4000.0, "costo_fallo_catastrofico": 32000.0},
        "Compresor Industrial B-2": {"desgaste": 15.0, "temp_c": 58.0, "vibracion_hz": 8.0, "horas": 210, "costo_reparacion": 1200.0, "costo_fallo_catastrofico": 9000.0}
    }

if "historial_finanzas" not in st.session_state:
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=15, freq="H")
    st.session_state.historial_finanzas = pd.DataFrame({
        "Tiempo": fechas,
        "Capital": [150000.0 + i * random.randint(-500, 2000) for i in range(15)],
        "Ingresos": [random.randint(4000, 12000) for _ in range(15)],
        "Costos_Variables": [random.randint(1500, 5000) for _ in range(15)]
    })

if "historial_alertas" not in st.session_state:
    st.session_state.historial_alertas = []

if "motor_activo" not in st.session_state:
    st.session_state.motor_activo = False

if "ultima_ejecucion" not in st.session_state:
    st.session_state.ultima_ejecucion = 0

# ---------------------------------------------------------
# BARRA LATERAL: CONFIGURACIÓN
# ---------------------------------------------------------
st.sidebar.title("⚙️ Configuración del Servidor")

st.sidebar.subheader("🔑 Credenciales de Notificación")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password", help="Consíguela en aistudio.google.com")
smtp_email = st.sidebar.text_input("Correo Remitente (SMTP):", value="pruebaprogramacionempresa@gmail.com")
smtp_password = st.sidebar.text_input("Contraseña de Aplicación:", type="password")
dest_email = st.sidebar.text_input("Correo Destinatario:", value="pruebaprogramacionempresa@gmail.com")

st.sidebar.markdown("---")
st.sidebar.subheader("🎚️ Umbrales de Seguridad")
sensibilidad_desgaste = st.sidebar.slider("Alerta por Desgaste Crítico (%):", 50, 95, 75)
sensibilidad_temp = st.sidebar.slider("Alerta Temperatura Crítica (°C):", 70, 120, 90)
frecuencia_monitoreo = st.sidebar.number_input("Frecuencia de ciclo (segundos):", min_value=10, value=30, step=5)

st.sidebar.markdown("---")
st.sidebar.subheader("Estado del Agente:")
if st.session_state.motor_activo:
    st.sidebar.markdown("🟢 **MONITOREO EN TIEMPO REAL ACTIVO**")
else:
    st.sidebar.markdown("🔴 **SISTEMA EN PAUSA**")

col_a1, col_a2 = st.sidebar.columns(2)
with col_a1:
    if st.button("▶️ Iniciar"):
        st.session_state.motor_activo = True
        st.rerun()
with col_a2:
    if st.button("⏹️ Detener"):
        st.session_state.motor_activo = False
        st.rerun()

# ---------------------------------------------------------
# FUNCIONES NÚCLEO (IA & COMUNICACIÓN)
# ---------------------------------------------------------
def consultar_gemini_agente(api_key, tipo_evento, contexto):
    """Consulta al modelo Gemini 2.0 Flash para auditorías técnicas y financieras."""
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Eres el Director Técnico e Inteligencia Artificial Supervisora de la empresa: {st.session_state.empresa_nombre}.
    
    TIPO DE INCIDENCIA DETECTADA: {tipo_evento}
    
    DATOS OPERATIVOS Y TELEMETRÍA EN TIEMPO REAL:
    {contexto}

    REQUERIMIENTOS DEL INFORME:
    1. **Diagnóstico Predictivo:** Analiza el riesgo y estima la Vida Útil Restante (RUL) o el impacto en tesorería.
    2. **Análisis de Impacto Económico:** Compara el costo de prevención inmediata vs. la pérdida total por paro de planta o falta de liquidez.
    3. **Plan de Acción Inmediato:** Proporciona 3 pasos ejecutivos claros dirigidos a la dirección de la empresa.
    4. **Tono:** Profesional, directo, tipo Toque de Atención Gerencial.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

def enviar_email_alerta(remitente, password, destinatario, asunto, cuerpo):
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

def ejecutar_simulacion_ciclo(forzar=None):
    """Avanza la telemetría y contabilidad de la empresa un paso en el tiempo."""
    # 1. Finanzas del ciclo
    ingresos_ciclo = random.randint(5000, 18000) if forzar != "pico_ventas" else random.randint(50000, 95000)
    gastos_variables = random.randint(2000, 7000)
    gastos_fijos_ciclo = sum(st.session_state.costos_fijos.values()) / 30  # Prorrateo diario/ciclo
    
    balance_neto = ingresos_ciclo - (gastos_variables + gastos_fijos_ciclo)
    st.session_state.capital += balance_neto
    
    # Registramos en el histórico financiero
    nueva_fila_fin = {
        "Tiempo": pd.Timestamp.now(),
        "Capital": st.session_state.capital,
        "Ingresos": ingresos_ciclo,
        "Costos_Variables": gastos_variables
    }
    st.session_state.historial_finanzas = pd.concat(
        [st.session_state.historial_finanzas, pd.DataFrame([nueva_fila_fin])], 
        ignore_index=True
    ).tail(25)

    # 2. Telemetría y Salud de Maquinaria
    maquina_riesgo = ""
    max_desgaste = 0.0
    temp_max = 0.0
    
    for nombre, datos in st.session_state.maquinaria.items():
        inc_desgaste = random.uniform(0.5, 2.5)
        inc_temp = random.uniform(-2.0, 3.0)
        
        if forzar == "averia_maquina" and nombre == "Línea de Corte Láser CNC":
            inc_desgaste = 32.0
            inc_temp = 25.0
            
        datos["desgaste"] = min(100.0, datos["desgaste"] + inc_desgaste)
        datos["temp_c"] = max(40.0, min(130.0, datos["temp_c"] + inc_temp))
        datos["vibracion_hz"] = round(random.uniform(10.0, 35.0), 1)
        datos["horas"] += random.randint(1, 5)

        if datos["desgaste"] > max_desgaste:
            max_desgaste = datos["desgaste"]
            maquina_riesgo = nombre
            temp_max = datos["temp_c"]

    # Evaluaciones de disparadores de alerta
    es_critico_desgaste = max_desgaste >= sensibilidad_desgaste
    es_critico_temp = temp_max >= sensibilidad_temp
    es_pico_ventas = ingresos_ciclo >= 45000

    return ingresos_ciclo, balance_neto, maquina_riesgo, max_desgaste, temp_max, (es_critico_desgaste or es_critico_temp), es_pico_ventas

# ---------------------------------------------------------
# INTERFAZ Y PESTAÑAS PRINCIPALES
# ---------------------------------------------------------
tab_dash, tab_sim, tab_config, tab_log = st.tabs([
    "📊 Panel de Control (ERP)", 
    "🧪 Laboratorio de Contingencias", 
    "⚙️ Parámetros de Empresa",
    "📜 Registro de Auditorías"
])

# --- PESTAÑA 1: DASHBOARD ERP ---
with tab_dash:
    st.subheader(f"Visión General Operativa: {st.session_state.empresa_nombre}")
    
    k1, k2, k3, k4 = st.columns(4)
    ult_ingreso = st.session_state.historial_finanzas["Ingresos"].iloc[-1]
    
    k1.metric("Capital Disponible", f"{st.session_state.capital:,.2f} €", f"{st.session_state.historial_finanzas['Capital'].iloc[-1] - st.session_state.historial_finanzas['Capital'].iloc[-2]:,.2f} €")
    k2.metric("Último Ingreso", f"{ult_ingreso:,.2f} €")
    k3.metric("Gastos Fijos Mensuales", f"{sum(st.session_state.costos_fijos.values()):,.2f} €")
    
    # Evaluación global de salud
    peor_maq = max(st.session_state.maquinaria.items(), key=lambda x: x[1]["desgaste"])
    if peor_maq[1]["desgaste"] >= sensibilidad_desgaste:
        k4.error(f"🚨 Riesgo: {peor_maq[0]} ({peor_maq[1]['desgaste']:.1f}%)")
    else:
        k4.success(f"🟢 Maquinaria Estable ({peor_maq[1]['desgaste']:.1f}%)")

    st.markdown("---")
    
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        fig_cap = px.area(
            st.session_state.historial_finanzas, 
            x="Tiempo", 
            y="Capital", 
            title="📈 Evolución de Tesorería y Liquidez (€)",
            template="plotly_dark"
        )
        fig_cap.update_traces(line_color="#00E676")
        st.plotly_chart(fig_cap, use_container_width=True)

    with g_col2:
        df_maq = pd.DataFrame([
            {"Equipo": k, "Desgaste_%": v["desgaste"], "Temp_°C": v["temp_c"]} 
            for k, v in st.session_state.maquinaria.items()
        ])
        fig_maq = px.bar(
            df_maq, 
            x="Equipo", 
            y="Desgaste_%", 
            color="Temp_°C",
            title="🛠️ Desgaste y Temperatura de Equipos Críticos",
            color_continuous_scale="OrRd",
            range_y=[0, 100],
            template="plotly_dark"
        )
        st.plotly_chart(fig_maq, use_container_width=True)

# --- PESTAÑA 2: LABORATORIO DE CONTINGENCIAS ---
with tab_sim:
    st.subheader("Simulación de Escenarios y Pruebas del Agente Predictivo")
    st.write("Usa estos mandos para forzar anomalías operativas y comprobar cómo la IA evalúa la telemetría antes de enviar el correo de alerta.")

    c_b1, c_b2, c_b3 = st.columns(3)
    
    with c_b1:
        if st.button("⚠️ Provocar Fallo Severo en CNC"):
            if not gemini_key or not smtp_email or not smtp_password or not dest_email:
                st.error("Completa las credenciales en la barra lateral.")
            else:
                ing, bal, maq, desg, temp, es_crit, es_pico = ejecutar_simulacion_ciclo(forzar="averia_maquina")
                with st.spinner("Gemini AI procesando diagnósticos de RUL y costos de reparación..."):
                    try:
                        info_maq = st.session_state.maquinaria[maq]
                        ctx = f"Equipo: {maq}\nDesgaste: {desg:.1f}%\nTemperatura: {temp:.1f} °C\nCosto Mantenimiento Preventivo: {info_maq['costo_reparacion']} €\nCosto Parada Catastrófica: {info_maq['costo_fallo_catastrofico']} €\nCapital Actual: {st.session_state.capital:,.2f} €"
                        
                        reporte = consultar_gemini_agente(gemini_key, "ALERTA PREDICTIVA: FALLO INMINENTE DE MAQUINARIA", ctx)
                        enviar_email_alerta(smtp_email, smtp_password, dest_email, f"🚨 URGENTE: Riesgo de Avería en {maq}", reporte)
                        
                        t_str = time.strftime('%H:%M:%S')
                        st.session_state.historial_alertas.append(f"[{t_str}] 🚨 Notificación enviada: Fallo inminente en {maq} ({desg:.1f}% Desgaste).")
                        st.success("¡Alerta generada y correo enviado con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en la llamada a Gemini: {e}")

    with c_b2:
        if st.button("💰 Simular Pico Excepcional de Ventas"):
            if not gemini_key or not smtp_email or not smtp_password or not dest_email:
                st.error("Completa las credenciales en la barra lateral.")
            else:
                ing, bal, maq, desg, temp, es_crit, es_pico = ejecutar_simulacion_ciclo(forzar="pico_ventas")
                with st.spinner("Analizando desviación positiva en flujo de caja..."):
                    try:
                        ctx = f"Ingreso Registrado: {ing:,.2f} €\nCapital Actual: {st.session_state.capital:,.2f} €"
                        reporte = consultar_gemini_agente(gemini_key, "INFORME FINANCIERO: PICO EXCEPCIONAL DE VENTAS", ctx)
                        enviar_email_alerta(smtp_email, smtp_password, dest_email, f"🚀 REGISTRO: Pico Extrahordinario de Ventas ({ing:,.2f} €)", reporte)
                        
                        t_str = time.strftime('%H:%M:%S')
                        st.session_state.historial_alertas.append(f"[{t_str}] 💰 Notificación enviada: Pico de ventas ({ing:,.2f} €).")
                        st.success("¡Informe de ganancias notificado por correo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en la llamada a Gemini: {e}")

    with c_b3:
        if st.button("🔧 Ejecutar Mantenimiento General"):
            for m in st.session_state.maquinaria.values():
                m["desgaste"] = 10.0
                m["temp_c"] = 50.0
            st.success("Se ha realizado el mantenimiento. Toda la maquinaria vuelve a niveles óptimos.")
            st.rerun()

# --- PESTAÑA 3: PARÁMETROS DE EMPRESA ---
with tab_config:
    st.subheader("Personalización del Perfil de la Empresa")
    st.write("Aquí las PYMES podrán configurar su estructura de costes reales.")
    
    st.session_state.empresa_nombre = st.text_input("Nombre Comercial de la Empresa:", value=st.session_state.empresa_nombre)
    st.session_state.capital = st.number_input("Capital/Tesorería Inicial (€):", value=float(st.session_state.capital), step=1000.0)
    
    st.markdown("#### Estructura de Costos Fijos Mensuales")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.session_state.costos_fijos["Nóminas Plantilla"] = st.number_input("Nóminas (€):", value=float(st.session_state.costos_fijos["Nóminas Plantilla"]))
        st.session_state.costos_fijos["Alquiler Nave Industrial"] = st.number_input("Alquiler Nave (€):", value=float(st.session_state.costos_fijos["Alquiler Nave Industrial"]))
    with col_c2:
        st.session_state.costos_fijos["Electricidad y Agua"] = st.number_input("Suministros (€):", value=float(st.session_state.costos_fijos["Electricidad y Agua"]))
        st.session_state.costos_fijos["Licencias y Seguros"] = st.number_input("Seguros y Licencias (€):", value=float(st.session_state.costos_fijos["Licencias y Seguros"]))

# --- PESTAÑA 4: HISTORIAL DE REGISTROS ---
with tab_log:
    st.subheader("Auditoría de Alertas Enviadas")
    if st.session_state.historial_alertas:
        for reg in reversed(st.session_state.historial_alertas):
            st.info(reg)
    else:
        st.info("Sin registros acumulados. El sistema permanecerá en silencio hasta que la IA detecte una anomalía crítica.")

# ---------------------------------------------------------
# BUCLE AUTÓNOMO 24/7 EN SEGUNDO PLANO
# ---------------------------------------------------------
if st.session_state.motor_activo:
    t_actual = time.time()
    if t_actual - st.session_state.ultima_ejecucion >= frecuencia_monitoreo:
        ing, bal, maq, desg, temp, es_crit, es_pico = ejecutar_simulacion_ciclo()
        st.session_state.ultima_ejecucion = t_actual
        
        # Evaluar disparo de alerta autónoma
        if (es_crit or es_pico) and gemini_key and smtp_email and smtp_password and dest_email:
            try:
                tipo_e = "RIESGO CRÍTICO DE AVERÍA EN MAQUINARIA" if es_crit else "PICO ANÓMALO DE VENTAS"
                info_m = st.session_state.maquinaria[maq]
                ctx = f"Equipo Afectado: {maq}\nDesgaste: {desg:.1f}%\nTemperatura: {temp:.1f} °C\nCapital: {st.session_state.capital:,.2f} €"
                
                reporte = consultar_gemini_agente(gemini_key, tipo_e, ctx)
                enviar_email_alerta(smtp_email, smtp_password, dest_email, f"🤖 AUTÓNOMO: {tipo_e}", reporte)
                
                t_s = time.strftime('%H:%M:%S')
                st.session_state.historial_alertas.append(f"[{t_s}] 🤖 Alerta Autónoma enviada debido a: {tipo_e}")
            except Exception as e:
                t_s = time.strftime('%H:%M:%S')
                st.session_state.historial_alertas.append(f"[{t_s}] ⚠️ Error en ciclo autónomo: {e}")

        st.rerun()

    time.sleep(2)
    st.rerun()
