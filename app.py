import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import time
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Industrias 24/7 - Panel Industrial Completo",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS MEJORADO - Diseño profesional y moderno
st.markdown("""
    <style>
        .main { background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 100%); }
        .metric-card {
            background: linear-gradient(145deg, #1e2235, #151929);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #2a2f45;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }
        .metric-card:hover { transform: translateY(-2px); border-color: #4a6cf7; }
        .metric-label { color: #8892b0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
        .metric-value { color: #ffffff; font-size: 2rem; font-weight: 700; margin: 8px 0; }
        .metric-delta { color: #64ffda; font-size: 0.9rem; }
        .metric-delta-negative { color: #ff6b6b; font-size: 0.9rem; }
        .section-title {
            color: #ccd6f6;
            font-size: 1.8rem;
            font-weight: 700;
            border-bottom: 2px solid #4a6cf7;
            padding-bottom: 10px;
            margin-bottom: 25px;
        }
        .section-subtitle { color: #8892b0; font-size: 1rem; margin-bottom: 20px; }
        .sidebar-logo { text-align: center; padding: 20px 0; }
        .sidebar-title { color: #ccd6f6; font-size: 1.5rem; font-weight: 700; text-align: center; }
        .sidebar-status {
            background: rgba(74, 108, 247, 0.1);
            border: 1px solid #4a6cf7;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .dataframe { background: #1a1a2e !important; border-radius: 8px !important; border: 1px solid #2a2f45 !important; }
        .dataframe th { background: #2a2f45 !important; color: #ccd6f6 !important; font-weight: 600 !important; }
        .dataframe td { color: #e6e6e6 !important; border-color: #2a2f45 !important; }
        .stButton > button {
            background: linear-gradient(135deg, #4a6cf7, #6a4cf7);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(74, 108, 247, 0.4); }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-critical { background: #ff6b6b; color: #0a0e1a; }
        .badge-warning { background: #ffc107; color: #0a0e1a; }
        .badge-optimal { background: #64ffda; color: #0a0e1a; }
        .progress-bar { height: 6px; border-radius: 3px; background: #2a2f45; margin: 8px 0; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
        .metric-container {
            background: rgba(26, 26, 46, 0.5);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid rgba(42, 47, 69, 0.3);
        }
        /* Estado de conexión */
        .status-connected {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            background: rgba(100, 255, 218, 0.1);
            border-radius: 8px;
            border: 1px solid #64ffda;
        }
        .status-disconnected {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            background: rgba(255, 107, 107, 0.1);
            border-radius: 8px;
            border: 1px solid #ff6b6b;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. FUNCIONES DE UTILIDAD PARA TENDENCIAS Y COLORES
# ---------------------------------------------------------

def calcular_tendencia(df, columna):
    """Calcula si el valor ha subido o bajado respecto al registro anterior"""
    if len(df) < 2:
        return "→", 0
    ultimo = df[columna].iloc[-1]
    anterior = df[columna].iloc[-2]
    cambio = ((ultimo - anterior) / anterior) * 100 if anterior != 0 else 0
    if cambio > 0:
        return "▲", cambio
    elif cambio < 0:
        return "▼", cambio
    else:
        return "→", 0

def color_desgaste(val):
    """Devuelve color según nivel de desgaste para la tabla"""
    if val > 60:
        return 'background-color: #ff4444; color: white; font-weight: bold;'
    elif val > 30:
        return 'background-color: #ffaa00; color: black; font-weight: bold;'
    else:
        return 'background-color: #00cc66; color: white; font-weight: bold;'

# ---------------------------------------------------------
# 3. CONEXIÓN A SUPABASE Y SECRETOS DE CORREO
# ---------------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

# Credenciales de Correo desde los Secrets de Streamlit
EMAIL_SENDER = st.secrets.get("EMAIL_SENDER", "")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = st.secrets.get("EMAIL_RECEIVER", "")
SMTP_SERVER = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(st.secrets.get("SMTP_PORT", 587))

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# ---------------------------------------------------------
# 4. FUNCIONES DE UTILIDAD Y ALERTAS POR CORREO
# ---------------------------------------------------------
def enviar_alerta_correo(asunto, cuerpo):
    """Envía un correo electrónico utilizando la configuración SMTP de los secrets."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
        return False  
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = asunto
        
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False

def cargar_datos_frescos():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("registros").select("*").order("created_at", desc=False).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'], format='mixed', errors='coerce')
            return df
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
    return pd.DataFrame()

def get_estado_empresa(df):
    if df.empty:
        return None
    ultimo = df.iloc[-1]
    return {
        'capital': float(ultimo.get("capital", 150000.0)),
        'ingreso': float(ultimo.get("ingreso", 0.0)),
        'desgaste_cnc': float(ultimo.get("desgaste_cnc", 10.0)),
        'fecha': ultimo.get("created_at", datetime.now())
    }

def calcular_metricas(estado):
    if not estado:
        return {}
    
    coste_estandar = 4000.0
    margen_valor = estado['ingreso'] - coste_estandar
    margen_porcentaje = (margen_valor / coste_estandar) * 100 if coste_estandar > 0 else 0.0
    oee_planta = max(40.0, 98.5 - (estado['desgaste_cnc'] * 0.45))
    
    if estado['desgaste_cnc'] >= 75.0:
        riesgo = ("🚨 CRÍTICO", "badge-critical")
    elif estado['desgaste_cnc'] >= 50.0:
        riesgo = ("⚠️ PRECAUCIÓN", "badge-warning")
    else:
        riesgo = ("✅ ÓPTIMO", "badge-optimal")
    
    salud = max(0, 100 - estado['desgaste_cnc'])
    
    return {
        'margen_valor': margen_valor,
        'margen_porcentaje': margen_porcentaje,
        'oee_planta': oee_planta,
        'riesgo': riesgo,
        'salud': salud,
        'coste_estandar': coste_estandar
    }

def crear_grafico_gauge(valor, titulo, min_val=0, max_val=100):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=valor,
        title={'text': titulo, 'font': {'color': '#ccd6f6', 'size': 14}},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickfont': {'color': '#8892b0'}},
            'bar': {'color': '#4a6cf7'},
            'steps': [
                {'range': [0, 30], 'color': 'rgba(100, 255, 218, 0.2)'},
                {'range': [30, 70], 'color': 'rgba(255, 193, 7, 0.2)'},
                {'range': [70, 100], 'color': 'rgba(255, 107, 107, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#ccd6f6'},
        height=250,
        margin=dict(t=30, b=0, l=0, r=0)
    )
    return fig

# ---------------------------------------------------------
# 5. CARGA DE DATOS Y COMPROBACIÓN DE ALERTAS
# ---------------------------------------------------------
df = cargar_datos_frescos()
estado = get_estado_empresa(df)
metricas = calcular_metricas(estado) if estado else {}

# Calcular tendencias si hay datos
if not df.empty and len(df) > 1:
    tendencia_capital, cambio_capital = calcular_tendencia(df, 'capital')
    tendencia_desgaste, cambio_desgaste = calcular_tendencia(df, 'desgaste_cnc')
    tendencia_ingreso, cambio_ingreso = calcular_tendencia(df, 'ingreso')
else:
    tendencia_capital = tendencia_desgaste = tendencia_ingreso = "→"
    cambio_capital = cambio_desgaste = cambio_ingreso = 0

# Alerta por correo si desgaste crítico
if estado and estado['desgaste_cnc'] >= 75.0:
    if "alerta_enviada" not in st.session_state:
        st.session_state["alerta_enviada"] = False

    if not st.session_state["alerta_enviada"]:
        asunto = "🚨 ALERTA CRÍTICA: Desgaste elevado en Maquinaria CNC"
        cuerpo = f"""Atención equipo de mantenimiento,

El sistema Industrias 24/7 ha detectado un nivel crítico en la línea de producción:

- Desgaste CNC: {estado['desgaste_cnc']:.1f}%
- Capital Operativo actual: {estado['capital']:,.0f} €
- Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Por favor, revisen el panel de control de inmediato."""
        
        exito = enviar_alerta_correo(asunto, cuerpo)
        if exito:
            st.session_state["alerta_enviada"] = True
else:
    st.session_state["alerta_enviada"] = False

# ---------------------------------------------------------
# 6. BARRA LATERAL MEJORADA
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <img src="https://img.icons8.com/color/96/factory.png" width="70">
            <div class="sidebar-title">🏭 Industrias 24/7</div>
            <div style="color: #8892b0; font-size: 0.8rem;">Sistema de Supervisión Industrial</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    menu = st.radio(
        "📌 Panel de Navegación",
        [
            "📊 Dashboard y KPIs",
            "📈 Gráficos Avanzados",
            "📋 Tabla de Registros",
            "🕹️ Simulación y Control"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### ⚡ Control en Vivo")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    with col2:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    st.markdown(f"""
        <div class="sidebar-status">
            <div style="color: #8892b0; font-size: 0.8rem;">Última comprobación</div>
            <div style="color: #64ffda; font-weight: 600;">{datetime.now().strftime('%H:%M:%S')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    if not df.empty:
        st.markdown(f"""
            <div class="sidebar-status">
                <div style="color: #8892b0; font-size: 0.8rem;">Registros totales</div>
                <div style="color: #4a6cf7; font-weight: 700; font-size: 1.2rem;">{len(df)}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if estado and metricas:
            st.markdown("---")
            st.markdown("### 📊 Estado del Sistema")
            
            salud = metricas['salud']
            color = "#64ffda" if salud > 70 else "#ffc107" if salud > 40 else "#ff6b6b"
            st.markdown(f"""
                <div style="margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; color: #8892b0; font-size: 0.8rem;">
                        <span>Salud Maquinaria</span>
                        <span style="color: {color}; font-weight: 600;">{salud:.0f}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {salud}%; background: {color};"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            riesgo_text, riesgo_class = metricas['riesgo']
            st.markdown(f"""
                <div style="text-align: center; margin-top: 10px;">
                    <span class="badge {riesgo_class}">{riesgo_text}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⏳ Esperando datos del worker...")
    
    # --- INDICADOR DE CONEXIÓN A SUPABASE ---
    st.markdown("---")
    st.markdown("### 🔌 Estado del Sistema")
    
    try:
        test = supabase.table("registros").select("count").limit(1).execute()
        st.markdown("""
            <div class="status-connected">
                <span style="color: #64ffda;">●</span>
                <span style="color: #ccd6f6;">Supabase conectado</span>
                <span style="margin-left: auto; font-size: 0.7rem; color: #64ffda;">✅</span>
            </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown("""
            <div class="status-disconnected">
                <span style="color: #ff6b6b;">●</span>
                <span style="color: #ccd6f6;">Supabase desconectado</span>
                <span style="margin-left: auto; font-size: 0.7rem; color: #ff6b6b;">❌</span>
            </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. CONTENIDO PRINCIPAL
# ---------------------------------------------------------

st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
            <div class="section-title">🏭 Panel de Control Industrial</div>
            <div class="section-subtitle">Monitorización en tiempo real de la línea de producción autónoma</div>
        </div>
        <div style="text-align: right;">
            <div style="color: #8892b0; font-size: 0.8rem;">Sistema conectado a Supabase</div>
            <div style="color: #64ffda; font-size: 0.8rem;">🟢 Activo</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 8. MENÚ: DASHBOARD Y KPIs
# ---------------------------------------------------------
if menu == "📊 Dashboard y KPIs":
    st.markdown("### 📊 KPIs Principales")
    
    if df.empty:
        st.warning("⏳ Esperando datos del worker autónomo en Supabase...")
        st.info("💡 El worker se ejecuta automáticamente cada 10 minutos a través de GitHub Actions")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">💰 Capital Operativo</div>
                    <div class="metric-value">{estado['capital']:,.0f} €</div>
                    <div class="metric-delta">
                        {tendencia_capital} {cambio_capital:.1f}% (último cambio)
                        <span style="color: #8892b0; font-size: 0.8rem;">| Ingreso: +{estado['ingreso']:,.0f} €</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            desgaste = estado['desgaste_cnc']
            color_delta = "metric-delta-negative" if desgaste > 50 else "metric-delta"
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">⚙️ Desgaste CNC</div>
                    <div class="metric-value">{desgaste:.1f}%</div>
                    <div class="{color_delta}">
                        {tendencia_desgaste} {cambio_desgaste:.1f}% | 
                        Estado: {'⚠️ Crítico' if desgaste > 70 else '⚠️ Atención' if desgaste > 40 else '✅ Normal'}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📈 OEE Planta</div>
                    <div class="metric-value">{metricas['oee_planta']:.1f}%</div>
                    <div class="metric-delta">Eficiencia global</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            riesgo_text, _ = metricas['riesgo']
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🚨 Nivel de Riesgo</div>
                    <div class="metric-value" style="font-size: 1.5rem;">{riesgo_text}</div>
                    <div class="metric-delta">Basado en desgaste CNC</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📈 Análisis Detallado")
        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #8892b0; font-size: 0.85rem;">📊 Margen del Turno</div>
                    <div style="color: #64ffda; font-size: 1.8rem; font-weight: 700;">{metricas['margen_porcentaje']:.1f}%</div>
                    <div style="color: #8892b0; font-size: 0.9rem;">{metricas['margen_valor']:,.0f} €</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #8892b0; font-size: 0.85rem;">🔧 Salud Maquinaria</div>
                    <div style="color: #4a6cf7; font-size: 1.8rem; font-weight: 700;">{metricas['salud']:.0f}%</div>
                    <div style="color: #8892b0; font-size: 0.9rem;">Índice de condición</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col7:
            st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #8892b0; font-size: 0.85rem;">📦 Último Ingreso</div>
                    <div style="color: #64ffda; font-size: 1.8rem; font-weight: 700;">{estado['ingreso']:,.0f} €</div>
                    <div style="color: #8892b0; font-size: 0.9rem;">Costo estándar: {metricas['coste_estandar']:,.0f} €</div>
                    <div style="color: #8892b0; font-size: 0.8rem;">{tendencia_ingreso} {cambio_ingreso:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Indicadores Visuales")
        col_g1, col_g2, col_g3 = st.columns(3)
        
        with col_g1:
            fig1 = crear_grafico_gauge(estado['desgaste_cnc'], "Desgaste CNC")
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_g2:
            fig2 = crear_grafico_gauge(metricas['salud'], "Salud Maquinaria")
            st.plotly_chart(fig2, use_container_width=True)
        
        with col_g3:
            fig3 = crear_grafico_gauge(metricas['oee_planta'], "OEE Planta")
            st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------------
# 9. MENÚ: GRÁFICOS AVANZADOS
# ---------------------------------------------------------
elif menu == "📈 Gráficos Avanzados":
    st.markdown("### 📈 Tendencias Históricas de Operación")
    
    if not df.empty:
        # --- FILTRO DE FECHAS ---
        st.markdown("### 📅 Filtrar por fecha")
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio = st.date_input(
                "Fecha de inicio", 
                value=df['created_at'].min() if not df.empty else datetime.now()
            )
        with col_fecha2:
            fecha_fin = st.date_input(
                "Fecha de fin", 
                value=df['created_at'].max() if not df.empty else datetime.now()
            )
        
        # Filtrar el DataFrame
        if not df.empty:
            df_filtrado_fechas = df[
                (df['created_at'].dt.date >= fecha_inicio) & 
                (df['created_at'].dt.date <= fecha_fin)
            ]
            
            if df_filtrado_fechas.empty:
                st.warning("⚠️ No hay datos en el rango de fechas seleccionado")
                df_graficos = df
            else:
                df_graficos = df_filtrado_fechas
                st.success(f"✅ Mostrando {len(df_graficos)} registros en el rango seleccionado")
        else:
            df_graficos = df
        
        # --- GRÁFICOS ---
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Capital Operativo", "Desgaste CNC", "Ingresos", "Análisis Combinado"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": True}]]
        )
        
        fig.add_trace(
            go.Scatter(x=df_graficos['created_at'], y=df_graficos['capital'],
                       name="Capital", line=dict(color="#64ffda", width=2),
                       fill='tozeroy', fillcolor='rgba(100, 255, 218, 0.1)'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df_graficos['created_at'], y=df_graficos['desgaste_cnc'],
                       name="Desgaste CNC", line=dict(color="#ff6b6b", width=2),
                       fill='tozeroy', fillcolor='rgba(255, 107, 107, 0.1)'),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(x=df_graficos['created_at'], y=df_graficos['ingreso'],
                   name="Ingresos", marker_color="#4a6cf7"),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df_graficos['created_at'], y=df_graficos['capital'],
                       name="Capital", line=dict(color="#64ffda", width=2)),
            row=2, col=2
        )
        fig.add_trace(
            go.Scatter(x=df_graficos['created_at'], y=df_graficos['desgaste_cnc'] * 1000,
                       name="Desgaste (escalado)", line=dict(color="#ff6b6b", width=2, dash="dash")),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color="#ccd6f6",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_xaxes(title_text="Fecha", tickfont=dict(color="#8892b0"))
        fig.update_yaxes(title_text="Valor", tickfont=dict(color="#8892b0"))
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📊 Estadísticas Descriptivas")
        col_est1, col_est2, col_est3 = st.columns(3)
        
        with col_est1:
            st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #8892b0;">Capital</div>
                    <div style="color: #64ffda; font-weight: 700;">Mín: {df_graficos['capital'].min():,.0f} €</div>
                    <div style="color: #64ffda; font-weight: 700;">Máx: {df_graficos['capital'].max():,.0f} €</div>
                    <div style="color: #8892b0;">Media: {df_graficos['capital'].mean():,.0f} €</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_est2:
            st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #8892b0;">Desgaste CNC</div>
                    <div style="color: #ff6b6b; font-weight: 700;">Mín: {df_graficos['desgaste_cnc'].min():.1f}%</div>
                    <div style="color: #ff6b6b; font-weight: 700;">Máx: {df_graficos['desgaste_cnc'].max():.1f}%</div>
                    <div style="color: #8892b0;">Media: {df_graficos['desgaste_cnc'].mean():.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_est3:
            st.markdown(f"""
                <div class="metric-container">
                    <div style="color: #8892b0;">Ingresos</div>
                    <div style="color: #4a6cf7; font-weight: 700;">Mín: {df_graficos['ingreso'].min():,.0f} €</div>
                    <div style="color: #4a6cf7; font-weight: 700;">Máx: {df_graficos['ingreso'].max():,.0f} €</div>
                    <div style="color: #8892b0;">Media: {df_graficos['ingreso'].mean():,.0f} €</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💡 No hay datos suficientes para mostrar gráficos")

# ---------------------------------------------------------
# 10. MENÚ: TABLA DE REGISTROS
# ---------------------------------------------------------
elif menu == "📋 Tabla de Registros":
    st.markdown("### 📋 Historial Completo en Bruto")
    st.markdown("*Tabla detallada con todos los registros volcados de forma autónoma por el worker*")
    
    if not df.empty:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search = st.text_input("🔍 Buscar por ID", placeholder="Ej: 1, 2, 3...")
        with col_f2:
            min_capital = st.number_input("Capital mínimo", min_value=0, value=0, step=1000)
        with col_f3:
            max_desgaste = st.slider("Desgaste máximo", 0, 100, 100)
        
        df_filtrado = df.copy()
        if search:
            df_filtrado = df_filtrado[df_filtrado['id'].astype(str).str.contains(search)]
        if min_capital > 0:
            df_filtrado = df_filtrado[df_filtrado['capital'] >= min_capital]
        if max_desgaste < 100:
            df_filtrado = df_filtrado[df_filtrado['desgaste_cnc'] <= max_desgaste]
        
        # --- TABLA CON COLORES EN DESGASTE ---
        styled_df = df_filtrado.sort_values(by="created_at", ascending=False).style.applymap(
            color_desgaste, subset=['desgaste_cnc']
        )
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            column_config={
                "id": "ID",
                "created_at": "Fecha",
                "capital": st.column_config.NumberColumn("Capital", format="%.2f €"),
                "ingreso": st.column_config.NumberColumn("Ingreso", format="%.2f €"),
                "desgaste_cnc": st.column_config.NumberColumn("Desgaste CNC", format="%.1f %%")
            }
        )
        
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Descargar CSV",
                data=csv,
                file_name=f'historial_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                mime='text/csv',
                use_container_width=True
            )
        with col_exp2:
            st.info(f"📊 Mostrando {len(df_filtrado)} de {len(df)} registros")
    else:
        st.warning("No hay registros disponibles")

# ---------------------------------------------------------
# 11. MENÚ: SIMULACIÓN Y CONTROL
# ---------------------------------------------------------
elif menu == "🕹️ Simulación y Control":
    st.markdown("### 🕹️ Panel de Simulación y Control Activo")
    st.markdown("*Interactúa directamente con la línea de producción enviando eventos personalizados*")
    
    if df.empty:
        st.warning("No hay datos base para simular acciones.")
    else:
        ultimo = df.iloc[-1]
        cap_base = float(ultimo.get("capital", 150000.0))
        desg_base = float(ultimo.get("desgaste_cnc", 10.0))
        
        st.markdown("### 📊 Estado Actual de la Línea")
        col_act1, col_act2, col_act3 = st.columns(3)
        with col_act1:
            st.metric("Capital Base", f"{cap_base:,.0f} €")
        with col_act2:
            st.metric("Desgaste Actual", f"{desg_base:.1f}%")
        with col_act3:
            st.metric("Último Ingreso", f"{float(ultimo.get('ingreso', 0)):,.0f} €")
        
        st.markdown("---")
        st.markdown("### 🛠️ Acciones de Simulación")
        
        col_sim1, col_sim2 = st.columns(2)
        
        with col_sim1:
            st.markdown("""
                <div style="background: rgba(255, 107, 107, 0.1); padding: 20px; border-radius: 10px; border: 1px solid rgba(255, 107, 107, 0.3);">
                    <h4 style="color: #ff6b6b;">🚨 Simular Fallo Crítico</h4>
                    <p style="color: #8892b0; font-size: 0.9rem;">Fuerza un fallo mecánico imprevisto que eleva el desgaste y genera costes extraordinarios.</p>
            """, unsafe_allow_html=True)
            
            with st.form("fallo_form"):
                intensidad = st.slider("Intensidad del fallo", 20, 50, 35, help="Aumento del desgaste CNC")
                coste = st.number_input("Coste de reparación (€)", min_value=0, value=12000, step=1000)
                submitted = st.form_submit_button("💥 Provocar Avería", use_container_width=True)
                
                if submitted:
                    nuevo_desgaste = min(100.0, desg_base + intensidad)
                    nuevo_capital = cap_base - coste
                    try:
                        supabase.table("registros").insert({
                            "capital": round(nuevo_capital, 2),
                            "ingreso": 1500.0,
                            "desgaste_cnc": round(nuevo_desgaste, 2)
                        }).execute()
                        st.success("✅ ¡Avería simulada con éxito!")
                        st.info(f"📊 Desgaste: {desg_base:.1f}% → {nuevo_desgaste:.1f}% | Capital: {cap_base:,.0f}€ → {nuevo_capital:,.0f}€")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al registrar avería: {e}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_sim2:
            st.markdown("""
                <div style="background: rgba(100, 255, 218, 0.1); padding: 20px; border-radius: 10px; border: 1px solid rgba(100, 255, 218, 0.3);">
                    <h4 style="color: #64ffda;">🔧 Aplicar Mantenimiento</h4>
                    <p style="color: #8892b0; font-size: 0.9rem;">Envía al equipo técnico a reparar el sistema: reduce el desgaste aplicando el coste de reparación.</p>
            """, unsafe_allow_html=True)
            
            with st.form("mantenimiento_form"):
                nivel_reparacion = st.slider("Nivel de reparación", 0, 100, 85, help="% de reducción del desgaste")
                coste_mantenimiento = st.number_input("Coste de mantenimiento (€)", min_value=0, value=6500, step=500)
                submitted = st.form_submit_button("🔧 Ejecutar Mantenimiento", use_container_width=True)
                
                if submitted:
                    reduccion = (desg_base * nivel_reparacion) / 100
                    nuevo_desgaste = max(5.0, desg_base - reduccion)
                    nuevo_capital = cap_base - coste_mantenimiento
                    ingreso_reparacion = 4500.0
                    try:
                        supabase.table("registros").insert({
                            "capital": round(nuevo_capital, 2),
                            "ingreso": round(ingreso_reparacion, 2),
                            "desgaste_cnc": round(nuevo_desgaste, 2)
                        }).execute()
                        st.success("✅ ¡Mantenimiento aplicado con éxito!")
                        st.info(f"📊 Desgaste: {desg_base:.1f}% → {nuevo_desgaste:.1f}% | Capital: {cap_base:,.0f}€ → {nuevo_capital:,.0f}€")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al registrar mantenimiento: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 12. BUCLE DE AUTO-REFRESCO
# ---------------------------------------------------------
if auto_refresh:
    time.sleep(10)
    st.rerun()
