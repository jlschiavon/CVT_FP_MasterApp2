import streamlit as st

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# Estilos CSS para personalizar la UI
st.markdown("""
    <style>
        /* Panel lateral */
        .sidebar .sidebar-content {
            background-color: #f0f0f0;
            padding: 20px;
            border-radius: 15px;
        }
        /* Botones personalizados */
        .stButton>button {
            width: 100%;
            background-color: #3DAE2B;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            cursor: pointer;
        }
        .stButton>button:hover {
            background-color: #2d8c20;
        }
    </style>
""", unsafe_allow_html=True)

# Menú lateral
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/3/3a/Schaeffler_logo.svg", width=200)
st.sidebar.title("Menu")

# Diccionario de secciones
sections = {
    "OEE": "🔹 Aquí se mostrarán los indicadores de OEE",
    "Production": "📦 Producción por turno y día",
    "Scrap": "❌ Registro de Scrap",
    "Machine Breakdowns": "⚙️ Paros de máquina",
    "Oil Tracking": "🛢️ Seguimiento de aceite",
    "Negative": "📉 Datos negativos o pérdidas"
}

# Variable para almacenar sección activa
if "section" not in st.session_state:
    st.session_state.section = "OEE"

# Renderizamos botones
for sec in sections.keys():
    if st.sidebar.button(sec):
        st.session_state.section = sec

# Contenido dinámico según sección activa
st.markdown(f"## {st.session_state.section}")
st.write(sections[st.session_state.section])
