import streamlit as st

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# Estilos CSS para personalizar la UI
st.markdown("""
    <style>
        /* Fondo general */
        .main {
            background-color: #D9D9D9; /* gris claro */
        }

        /* Panel lateral */
        section[data-testid="stSidebar"] {
            background-color: #650000; /* gris oscuro */
            padding: 20px;
        }
        
        /* Botones personalizados */
        .stButton>button {
            width: 100%;
            background-color: #2F852C;
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

        /* Rectángulo superior */
        .top-banner {
            background-color: #2F852C;
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: left;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Menú lateral

st.sidebar.title("Menu")

# Diccionario de secciones
sections = {
    "Principal": "Página Principal",
    "OEE": "🔹 Aquí se mostrarán los indicadores de OEE",
    "Production": "📦 Producción por turno y día",
    "Scrap": "❌ Registro de Scrap",
    "Machine Breakdowns": "⚙️ Paros de máquina",
    "Oil Tracking": "🛢️ Seguimiento de aceite",
    "Negative": "📉 Datos negativos o pérdidas"
}

# Variable para almacenar sección activa
if "section" not in st.session_state:
    st.session_state.section = "Principal"

# Input para definir el texto del banner
banner_text = "CVT Final Processes"
st.markdown(f"<div class='top-banner'>{banner_text}</div>", unsafe_allow_html=True)

# Renderizamos botones
for sec in sections.keys():
    if st.sidebar.button(sec):
        st.session_state.section = sec

# Contenido dinámico según sección activa
st.markdown(f"## {st.session_state.section}")
st.write(sections[st.session_state.section])
