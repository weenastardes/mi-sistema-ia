import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import time

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Industrias 24/7 - Panel Industrial Completo",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. CONEXIÓN A SUPABASE
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
# 3. CARGA DE DATOS EN TIEMPO REAL
# ---------------------------------------------------------
def cargar_datos_frescos():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("estado_empresa").select("*").order("created_at", desc=False).execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
    return pd.DataFrame()

df = cargar_datos_frescos()

# ---------------------------------------------------------
# 4. BARRA LATERAL (CONTROLES Y ESTADO)
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/factory.png", width=60)
    st.title("Supervisión 24/7")
    st.markdown("---")
    
    menu = st.radio(
        "Panel de Navegación",
        ["📊 Dashboard y KPIs", "📈 Gráficos Avanzados", "📋 Tabla de Registros", "⚙️ Configuración"]
    )
    
    st.markdown("---")
    st.markdown("### ⚡ Control en Vivo")
    
    auto_refresh = st.checkbox("Activar auto-refresco (10s)", value=True)
    
    if st.button("🔄 Refrescar Ahora"):
        st.rerun()
        
    st.markdown(f"**Última comprobación:**\n`{datetime.now().strftime('%H:%M:%S')}`")
    
    if not df.empty:
        st.success(f"Registros totales: {len(df)}")
    else:
        st.warning("Sin registros en la BD")

# ---------------------------------------------------------
# 5. CONTENIDO PRINCIPAL DE LA VISTA
# ---------------------------------------------------------

if menu == "📊 Dashboard y KPIs":
    st.title("🏭 Panel de Control y Rendimiento Industrial")
    st.markdown("Monitorización en vivo de la línea de producción autónoma vinculada a Supabase.")

    if df.empty:
        st.warning("⏳ Esperando datos del worker autónomo en Supabase...")
    else:
        ultimo = df.iloc[-1]
        capital_actual = float(ultimo.get("capital", 150000.0))
        desgaste_actual = float(ultimo.get("desgaste_cnc", 10.0))
        ingreso_actual = float(ultimo.get("ingreso", 0.0))
        
        coste_estandar = 4000.0
        margen_valor = ingreso_actual - coste_estandar
        margen_porcentaje = (margen_valor / coste_estandar) * 100 if coste_estandar > 0 else 0.0
        oee_planta = max(40.0, 98.5 - (desgaste_actual * 0.45))
        
        nivel_riesgo = "🚨 CRÍTICO" if desgaste_actual >= 75.0 else ("⚠️ PRECAUCIÓN" if desgaste_actual >= 50.0 else "✅ ÓPTIMO")

        # KPIs Destacados
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Capital Operativo", f"{capital_actual:,.2f} €", f"{ingreso_actual:,.2f} € rec.")
        k2.metric("Desgaste CNC", f"{desgaste_actual:.1f} %", "Salud Maquinaria", delta_color="inverse" if desgaste_actual >= 75 else "normal")
        k3.metric("OEE Planta", f"{oee_planta:.1f} %", "Eficiencia")
        k4.metric("Margen Turno", f"{margen_porcentaje:.1f} %", f"{margen_valor:,.2f} €")
        k5.metric("Riesgo", nivel_riesgo)

        st.divider()

        # Resumen rápido visual
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.subheader("💡 Estado Operativo Actual")
            st.info(f"El sistema se encuentra operando bajo un nivel de riesgo **{nivel_riesgo}**. El último ciclo generó un ingreso de **{ingreso_actual:,.2f} €** con un desgaste acumulado en la línea CNC del **{desgaste_actual:.1f}%**.")
        with col_r2:
            st.subheader("🛠️ Acciones del Worker")
            st.success("El worker en GitHub Actions se ejecuta cada 5 minutos de forma autónoma alterando las variables estocásticas de producción y guardándolas directamente aquí.")

elif menu == "📈 Gráficos Avanzados":
    st.title("📈 Tendencias Históricas de Operación")
    st.markdown("Análisis gráfico independiente de los valores financieros y de desgaste mecánico.")

    if df.empty:
        st.warning("No hay datos suficientes para mostrar los gráficos.")
    else:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### 📈 Evolución del Capital Operativo (€)")
            if "capital" in df.columns:
                st.line_chart(df[["created_at", "capital"]].set_index("created_at"), color="#2563eb")
        with col_g2:
            st.markdown("#### 📉 Evolución del Desgaste CNC (%)")
            if "desgaste_cnc" in df.columns:
                st.area_chart(df[["created_at", "desgaste_cnc"]].set_index("created_at"), color="#dc2626")

elif menu == "📋 Tabla de Registros":
    st.title("📋 Historial Completo en Bruto")
    st.markdown("Tabla detallada con todos los registros volcados de forma autónoma por el worker.")
    
    if df.empty:
        st.warning("No hay registros disponibles en la base de datos.")
    else:
        # Mostramos los registros ordenados del más reciente al más antiguo para mayor comodidad
        st.dataframe(df.sort_values(by="created_at", ascending=False), use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Historial en CSV",
            data=csv,
            file_name='historial_industrial_supabase.csv',
            mime='text/csv',
        )

elif menu == "⚙️ Configuración":
    st.title("⚙️ Configuración y Estado del Sistema")
    st.markdown("""
    Este panel interactúa en tiempo real con la infraestructura de la empresa:
    - **Worker Autónomo:** Ejecutándose en segundo plano en GitHub Actions.
    - **Base de Datos:** Aloja la tabla `estado_empresa` en Supabase.
    """)
    st.json({
        "Supabase Conectado": bool(supabase),
        "Total Entradas en Tabla": len(df) if not df.empty else 0,
        "Última Sincronización": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# ---------------------------------------------------------
# 6. BUCLE DE AUTO-REFRESCO AUTOMÁTICO (STREAMING)
# ---------------------------------------------------------
if auto_refresh:
    time.sleep(10)
    st.rerun()
