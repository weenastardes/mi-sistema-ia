import streamlit as st
import pandas as pd
from supabase import create_client

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Industrias Innovación S.L. - Control 24/7",
    page_icon="🏭",
    layout="wide"
)

# Estilo visual general corporativo
st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .metric-card { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
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
# CARGA DE DATOS DESDE LA BASE DE DATOS
# ---------------------------------------------------------
def cargar_datos():
    if not supabase:
        # Datos simulados por defecto si no hay conexión para que la app no rompa visualmente
        return pd.DataFrame({
            "created_at": ["2026-06-07 10:00:00", "2026-06-07 10:05:00"],
            "capital": [150000.0, 154500.0],
            "ingreso": [5000.0, 6200.0],
            "desgaste_cnc": [10.0, 11.2]
        })
    try:
        response = supabase.table("estado_empresa").select("*").order("created_at", desc=False).execute()
        if response.data and len(response.data) > 0:
            return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
    
    return pd.DataFrame(columns=["created_at", "capital", "ingreso", "desgaste_cnc"])

df = cargar_datos()

# ---------------------------------------------------------
# ENCABEZADO Y BOTÓN DE REFRESCO MANUAL
# ---------------------------------------------------------
st.title("🏭 Panel de Control y Supervisión Industrial Autónoma")
st.markdown("Monitorización en tiempo real conectada a GitHub Actions y Supabase.")

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("🔄 Refrescar Datos"):
        st.cache_resource.clear()
        st.rerun()

if df.empty:
    st.warning("No hay registros disponibles en la base de datos todavía. Ejecuta el worker o espera al ciclo autónomo.")
    st.stop()

# Obtener el registro más reciente (último estado)
ultimo = df.iloc[-1]
capital_actual = float(ultimo.get("capital", 150000.0))
desgaste_actual = float(ultimo.get("desgaste_cnc", 10.0))
ingreso_actual = float(ultimo.get("ingreso", 0.0))

# Cálculo seguro y coherente del Margen del Turno (basado en ingresos netos vs costes estándar)
coste_turno_estandar = 4000.0
margen_turno_valor = ingreso_actual - coste_turno_estandar
margen_porcentaje = (margen_turno_valor / coste_turno_estandar) * 100 if coste_turno_estandar > 0 else 0.0

# OEE de planta simulado de manera realista en función del desgaste del CNC
oee_planta = max(65.0, 98.0 - (desgaste_actual * 0.35))

# Nivel de riesgo según el desgaste
if desgaste_actual >= 75.0:
    nivel_riesgo = "🚨 CRÍTICO"
    color_riesgo = "error"
elif desgaste_actual >= 50.0:
    nivel_riesgo = "⚠️ PRECAUCIÓN"
    color_riesgo = "warning"
else:
    nivel_riesgo = "✅ NOMINAL"
    color_riesgo = "success"

# ---------------------------------------------------------
# MÉTRICAS PRINCIPALES (KPIs SUPERIOR)
# ---------------------------------------------------------
st.markdown("### 📊 Indicadores Clave de Operación (KPIs)")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(label="Capital Operativo", value=f"{capital_actual:,.2f} €", delta=f"{ingreso_actual:,.2f} € último ingreso")

with kpi2:
    st.metric(label="Desgaste CNC", value=f"{desgaste_actual:.1f} %", delta="Salud Maquinaria" if desgaste_actual < 50 else "Revisión requerida", delta_color="inverse" if desgaste_actual >= 50 else "normal")

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
        chart_data_capital = df[["created_at", "capital"]].set_index("created_at")
        st.line_chart(chart_data_capital, color="#1f77b4")
    else:
        st.info("No hay datos históricos de capital.")

with col_g2:
    st.markdown("#### ⚙️ Evolución del Desgaste de Maquinaria (%)")
    if "desgaste_cnc" in df.columns:
        chart_data_desgaste = df[["created_at", "desgaste_cnc"]].set_index("created_at")
        st.area_chart(chart_data_desgaste, color="#ff4b4b")
    else:
        st.info("No hay datos históricos de desgaste.")

# ---------------------------------------------------------
# TABLA DE REGISTROS DETALLADOS
# ---------------------------------------------------------
with st.expander("🔍 Ver registros detallados en bruto (Base de Datos Supabase)"):
    st.dataframe(df, use_container_width=True)
