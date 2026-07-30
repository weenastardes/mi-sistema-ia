import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Industrias 24/7 - Panel de Control Autónomo",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS modernos para tarjetas y diseño industrial
st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. CONEXIÓN SEGURA A SUPABASE
# ---------------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# ---------------------------------------------------------
# 3. BARRA LATERAL (SIDEBAR)
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/factory.png", width=60)
    st.title("Supervisión 24/7")
    st.markdown("---")
    
    menu = st.radio(
        "Panel de Navegación",
        ["📊 Dashboard Industrial", "📋 Registros de Base de Datos", "ℹ️ Estado del Sistema"]
    )
    
    st.markdown("---")
    st.markdown("### 🔄 Control de Datos")
    if st.button("🔄 Refrescar Datos de Planta"):
        st.cache_resource.clear()
        st.rerun()
        
    st.markdown("---")
    st.markdown("**Estado de Conexión:**")
    if supabase:
        st.success("🟢 Supabase Conectado")
    else:
        st.error("🔴 Sin conexión a Supabase")
        
    st.text(f"Última actualización:\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ---------------------------------------------------------
# 4. CARGA DE DATOS DESDE SUPABASE
# ---------------------------------------------------------
@st.cache_data(ttl=10)
def cargar_datos_industriales():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("estado_empresa").select("*").order("created_at", desc=False).execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al consultar Supabase: {e}")
    return pd.DataFrame()

df = cargar_datos_industriales()

# ---------------------------------------------------------
# 5. VISTAS DE LA APLICACIÓN
# ---------------------------------------------------------

if menu == "📊 Dashboard Industrial":
    st.title("🏭 Panel de Control y Rendimiento Industrial")
    st.markdown("Monitorización en tiempo real de la línea de producción autónoma (GitHub Actions + Supabase).")
    
    if df.empty:
        st.warning("⏳ Esperando datos del worker autónomo... La base de datos aún no contiene registros.")
    else:
        # Extraer el último estado (última fila)
        ultimo = df.iloc[-1]
        capital_actual = float(ultimo.get("capital", 150000.0))
        desgaste_actual = float(ultimo.get("desgaste_cnc", 10.0))
        ingreso_actual = float(ultimo.get("ingreso", 0.0))
        
        # Indicadores derivados de negocio y planta
        coste_estandar = 4000.0
        margen_valor = ingreso_actual - coste_estandar
        margen_porcentaje = (margen_valor / coste_estandar) * 100 if coste_estandar > 0 else 0.0
        oee_planta = max(40.0, 98.5 - (desgaste_actual * 0.45))
        
        # Clasificación de riesgo
        if desgaste_actual >= 75.0:
            nivel_riesgo = "🚨 CRÍTICO"
        elif desgaste_actual >= 50.0:
            nivel_riesgo = "⚠️ PRECAUCIÓN"
        else:
            nivel_riesgo = "✅ ÓPTIMO"

        # --- SECCIÓN DE KPIS / MÉTRICAS PRINCIPALES ---
        st.markdown("### 📊 Indicadores Clave de Operación (KPIs)")
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        with kpi1:
            st.metric("Capital Operativo", f"{capital_actual:,.2f} €", f"{ingreso_actual:,.2f} € último ingreso")
        with kpi2:
            st.metric("Desgaste CNC", f"{desgaste_actual:.1f} %", "Salud Maquinaria", delta_color="inverse" if desgaste_actual >= 75 else "normal")
        with kpi3:
            st.metric("OEE de Planta", f"{oee_planta:.1f} %", "Eficiencia Global")
        with kpi4:
            st.metric("Margen del Turno", f"{margen_porcentaje:.1f} %", f"{margen_valor:,.2f} €")
        with kpi5:
            st.metric("Estado de Riesgo", nivel_riesgo)

        st.divider()

        # --- SECCIÓN DE GRÁFICOS SEPARADOS E INDEPENDIENTES ---
        st.markdown("### 📈 Tendencias Históricas de Operación")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### Evolución del Capital Operativo (€)")
            if "capital" in df.columns:
                chart_cap = df[["created_at", "capital"]].set_index("created_at")
                st.line_chart(chart_cap, color="#2563eb")
            else:
                st.info("No hay datos de capital disponibles.")
                
        with col_g2:
            st.markdown("#### Evolución del Desgaste de Maquinaria (%)")
            if "desgaste_cnc" in df.columns:
                chart_des = df[["created_at", "desgaste_cnc"]].set_index("created_at")
                st.area_chart(chart_des, color="#dc2626")
            else:
                st.info("No hay datos de desgaste disponibles.")

elif menu == "📋 Registros de Base de Datos":
    st.title("📋 Historial Completo en Bruto")
    st.markdown("Tabla detallada con todos los registros volcados de forma autónoma por el worker en Supabase.")
    
    if df.empty:
        st.warning("No hay registros en la base de datos actualmente.")
    else:
        st.dataframe(df, use_container_width=True)
        
        # Botón de exportación rápida a CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Historial en CSV",
            data=csv,
            file_name='historial_industrial_supabase.csv',
            mime='text/csv',
        )

elif menu == "ℹ️ Estado del Sistema":
    st.title("ℹ️ Arquitectura y Diagnóstico del Sistema")
    st.markdown("""
    Este panel forma parte de una infraestructura industrial autónoma orientada a la supervisión 24/7:
    - **Worker Autónomo (`worker.py`):** Ejecutado en segundo plano mediante GitHub Actions de forma periódica. Genera variables estocásticas de ingresos y desgaste mecánico.
    - **Base de Datos en la Nube (Supabase):** Almacena de forma persistente cada ciclo operativo sin intervención humana.
    - **Interfaz de Visualización (Streamlit):** Panel pasivo en tiempo real que refleja el estado actual de la planta industrial.
    """)
    
    st.info("Para verificar que el sistema autónomo sigue escribiendo nuevos datos, comprueba los registros de GitHub Actions o consulta la tabla en Supabase.")
