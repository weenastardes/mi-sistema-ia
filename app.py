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
        ["📊 Dashboard y KPIs", "📈 Gráficos Avanzados", "📋 Tabla de Registros", "🕹️ Simulación y Control Activo"]
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

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Capital Operativo", f"{capital_actual:,.2f} €", f"{ingreso_actual:,.2f} € rec.")
        k2.metric("Desgaste CNC", f"{desgaste_actual:.1f} %", "Salud Maquinaria", delta_color="inverse" if desgaste_actual >= 75 else "normal")
        k3.metric("OEE Planta", f"{oee_planta:.1f} %", "Eficiencia")
        k4.metric("Margen Turno", f"{margen_porcentaje:.1f} %", f"{margen_valor:,.2f} €")
        k5.metric("Riesgo", nivel_riesgo)

elif menu == "📈 Gráficos Avanzados":
    st.title("📈 Tendencias Históricas de Operación")
    if not df.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### 📈 Evolución del Capital Operativo (€)")
            st.line_chart(df[["created_at", "capital"]].set_index("created_at"), color="#2563eb")
        with col_g2:
            st.markdown("#### 📉 Evolución del Desgaste CNC (%)")
            st.area_chart(df[["created_at", "desgaste_cnc"]].set_index("created_at"), color="#dc2626")

elif menu == "📋 Tabla de Registros":
    st.title("📋 Historial Completo en Bruto")
    if not df.empty:
        st.dataframe(df.sort_values(by="created_at", ascending=False), use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar CSV", data=csv, file_name='historial.csv', mime='text/csv')

elif menu == "🕹️ Simulación y Control Activo":
    st.title("🕹️ Panel de Pruebas y Resolución de Fallos")
    st.markdown("Interactúa directamente con la línea de producción enviando eventos personalizados a Supabase.")

    if df.empty:
        st.warning("No hay datos base para simular acciones.")
    else:
        ultimo = df.iloc[-1]
        cap_base = float(ultimo.get("capital", 150000.0))
        desg_base = float(ultimo.get("desgaste_cnc", 10.0))

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("🚨 Simular Fallo Crítico / Avería")
            st.write("Fuerza un fallo mecánico imprevisto que eleva el desgaste y genera costes extraordinarios de revisión.")
            if st.button("💥 Provocar Avería Mecánica"):
                nuevo_desgaste = min(100.0, desg_base + 35.0)
                nuevo_capital = cap_base - 12000.0 # Coste de la avería/parada
                try:
                    supabase.table("estado_empresa").insert({
                        "capital": round(nuevo_capital, 2),
                        "ingreso": 0.0,
                        "desgaste_cnc": round(nuevo_desgaste, 2)
                    }).execute()
                    st.success("¡Avería simulada con éxito! Revisa los KPIs y la caída de capital.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar avería: {e}")

        with c2:
            st.subheader("🛠️ Aplicar Mantenimiento / Solución")
            st.write("Envía al equipo técnico a reparar el sistema: reduce el desgaste casi al mínimo aplicando el coste de reparación.")
            if st.button("🔧 Ejecutar Mantenimiento Correctivo"):
                nuevo_desgaste = 5.0 # Se repara casi por completo
                nuevo_capital = cap_base - 6500.0 # Coste de la intervención técnica
                try:
                    supabase.table("estado_empresa").insert({
                        "capital": round(nuevo_capital, 2),
                        "ingreso": 4500.0, # Ligero ingreso post-reparación
                        "desgaste_cnc": round(nuevo_desgaste, 2)
                    }).execute()
                    st.success("¡Mantenimiento aplicado! Maquinaria reparada y costes descontados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar mantenimiento: {e}")

# ---------------------------------------------------------
# 6. BUCLE DE AUTO-REFRESCO
# ---------------------------------------------------------
if auto_refresh:
    time.sleep(10)
    st.rerun()
