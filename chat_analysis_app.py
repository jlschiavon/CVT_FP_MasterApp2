import streamlit as st

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# Estilos CSS para personalizar la UI
st.markdown("""
    <style>
        /* Fondo de la página (central) */
        div[data-testid="stAppViewContainer"] {
            background-color: #F5F5F5; /* gris claro */
        }

        /* Panel lateral */
        section[data-testid="stSidebar"] {
            background-color: #626262; /* gris oscuro */
            padding: 20px;
            border-radius: 20px
        }

        .sidebar-box {
            background-color: #444444; /* gris un poco más claro para contraste */
            padding: 15px;
            border-radius: 12px;
            margin-top: 20px;
        }
        
        /* Botones personalizados */
        .stButton>button {
            width: 100% !important;
            background-color: #2F852C;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 7px;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 7px;
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
# Caja interna con color
with st.sidebar:
    st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)

    if st.button("OEE"):
        st.session_state.section = "OEE"
    if st.button("Producción"):
        st.session_state.section = "Production"
    if st.button("Scrap"):
        st.session_state.section = "Scrap"
    if st.button("Paros de máquina"):
        st.session_state.section = "Machine Breakdowns"
    if st.button("Aceite ATF"):
        st.session_state.section = "Oil Tracking"
    if st.button("Negativo"):
        st.session_state.section = "Negative"

    st.markdown('</div>', unsafe_allow_html=True)

# Contenido principal
st.title("Panel central")

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
