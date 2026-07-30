import os
import streamlit as st
import pandas as pd
from supabase import create_client

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Industrias Innovación S.L. - Control Avanzado",
    page_icon="🏭",
    layout="wide"
)

st.markdown("""
    <style>
        .main { background-color: #0e1117; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CONEXIÓN A SUPABASE
# ---------------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# ---------------------------------------------------------
# BARRA LATERAL: PANEL DE PRUEBAS Y SIMULACIÓN MANUAL
# ---------------------------------------------------------
st.sidebar.header("⚙️ Panel de Control y Pruebas")
st.sidebar.markdown("Fuerza parámetros al límite para comprobar el comportamiento del sistema y las alertas.")

modo_simulacion = st.sidebar.radio("Modo de Operación:", ["Automático (Supabase)", "Forzar Fallo Manual / Extremo"])

capital_manual = 150000.0
desgaste_manual = 10.0
ingreso_manual = 5000.0

if modo_simulacion == "Forzar Fallo Manual / Extremo":
    st.sidebar.subheader("🎛️ Parámetros de Estrés")
    capital_manual = st.sidebar.number_input("Capital Operativo (€)", value=125000.0, step=1000.0)
    desgaste_manual = st.sidebar.slider("Nivel de Desgaste CNC (%)", 0.0, 100.0, 85.0, step=1.0)
    ingreso_manual = st.sidebar.number_input("Ingreso del Turno (€)", value=1200.0, step=100.0)
    
    if st.sidebar.button("🚀 Aplicar Estado Forzado a Base de Datos"):
        if supabase:
            try:
                supabase.table("estado_empresa").insert({
                    "capital": capital_manual,
                    "ingreso": ingreso_manual,
                    "desgaste_cnc": desgaste_manual
                }).execute()
                st.sidebar.success("¡Estado crítico inyectado con éxito en Supabase!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error al insertar: {e}")
        else:
            st.sidebar.error("No hay conexión con Supabase configurada.")

st.sidebar.divider()
if st.sidebar.button("🔄 Refrescar Datos desde BD"):
    st.cache_resource.clear()
    st.rerun()

# ---------------------------------------------------------
# CARGA DE DATOS DESDE SUPABASE
# ---------------------------------------------------------
def cargar_datos():
    if not supabase:
        return pd.DataFrame({
            "created_at": ["2026-06-07 10:00:00"],
            "capital": [150000.0],
            "ingreso": [5000.0],
            "desgaste_cnc": [10.0]
        })
    try:
        response = supabase.table("estado_empresa").select("*").order("created_at", desc=False).execute()
        if response.data and len(response.data) > 0:
            return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
    
    return pd.DataFrame(columns=["created_at", "capital", "ingreso", "desgaste_cnc"])

df = cargar_datos()

# Definir valores actuales (si estamos en modo manual usamos los del slider, si no, el último de la BD)
if modo_simulacion == "Forzar Fallo Manual / Extremo":
    capital_actual = capital_manual
    desgaste_actual = desgaste_manual
    ingreso_actual = ingreso_manual
else:
    if not df.empty:
        ultimo = df.iloc[-1]
        capital_actual = float(ultimo.get("capital", 150000.0))
        desgaste_actual = float(ultimo.get("desgaste_cnc", 10.0))
        ingreso_actual = float(ultimo.get("ingreso", 0.0))
    else:
        capital_actual, desgaste_actual, ingreso_actual = 150000.0, 10.0, 5000.0

# ---------------------------------------------------------
# TÍTULO Y MÉTRICAS PRINCIPALES (KPIs)
# ---------------------------------------------------------
st.title("🏭 Centro de Inteligencia y Supervisión Industrial")
st.markdown("Monitorización en tiempo real y simulación de escenarios de estrés operativo.")

# Cálculos de negocio
coste_turno_estandar = 4000.0
margen_turno_valor = ingreso_actual - coste_turno_estandar
margen_porcentaje = (margen_turno_valor / coste_turno_estandar) * 100 if coste_turno_estandar > 0 else 0.0
oee_planta = max(50.0, 98.0 - (desgaste_actual * 0.4))

# Niveles de riesgo
if desgaste_actual >= 75.0:
    nivel_riesgo = "🚨 CRÍTICO (ALERTA)"
elif desgaste_actual >= 50.0:
    nivel_riesgo = "⚠️ PRECAUCIÓN"
else:
    nivel_riesgo = "✅ NOMINAL"

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(label="Capital Operativo", value=f"{capital_actual:,.2f} €", delta=f"{ingreso_actual:,.2f} € último ingreso")

with kpi2:
    st.metric(label="Desgaste CNC", value=f"{desgaste_actual:.1f} %", delta="Salud Maquinaria" if desgaste_actual < 75 else "¡Peligro de rotura!", delta_color="inverse" if desgaste_actual >= 75 else "normal")

with kpi3:
    st.metric(label="OEE de Planta", value=f"{oee_planta:.1f} %", delta="Eficiencia Global")

with kpi4:
    st.metric(label="Margen del Turno", value=f"{margen_porcentaje:.1f} %", delta=f"{margen_turno_valor:,.2f} €")

with kpi5:
    st.metric(label="Nivel de Riesgo", value=nivel_riesgo)

st.divider()

# ---------------------------------------------------------
# GRÁFICOS Y EVOLUCIÓN HISTÓRICA
# ---------------------------------------------------------
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("#### 📈 Historia de Capital Operativo (€)")
    if "capital" in df.columns:
        st.line_chart(df[["created_at", "capital"]].set_index("created_at"), color="#1f77b4")

with col_g2:
    st.markdown("#### ⚙️ Evolución del Desgaste de Maquinaria (%)")
    if "desgaste_cnc" in df.columns:
        st.area_chart(df[["created_at", "desgaste_cnc"]].set_index("created_at"), color="#ff4b4b")

# ---------------------------------------------------------
# TABLA DE REGISTROS
# ---------------------------------------------------------
with st.expander("🔍 Ver registros detallados en bruto (Base de Datos Supabase)"):
    st.dataframe(df, use_container_width=True)
