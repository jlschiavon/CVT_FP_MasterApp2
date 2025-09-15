import streamlit as st

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
        /* Fondo de la página central */
        div[data-testid="stAppViewContainer"] {
            background-color: #626262;
        }

        /* Panel lateral */
        section[data-testid="stSidebar"] {
            background-color: #D9D9D9;
            padding: 10px;
            border-radius: 20px;
        }

        /* Caja central */
        .central-box {
            background-color: #D9D9D9;
            padding: 15px;
            border-radius: 12px;
            margin-top: 20px;
        }
        
        /* Caja del menú lateral */
        .sidebar-box {
            background-color: #626262;
            padding: 15px;
            border-radius: 12px;
            margin-top: 20px;
        }

        /* Rectángulo superior */
        .top-banner {
            background-color: #2F852C;
            color: white;
            padding: 5px;
            border-radius: 10px;
            text-align: left;
            font-size: 35px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        /* Botones */
        .stButton>button {
            display: block;
            width: 100% !important;
            background-color: #2F852C;
            color: white;
            border: none;
            border-radius: 15px;
            padding: 6px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 5px;
            cursor: pointer;
        }
        .stButton>button:hover {
            background-color: #2d8c20;
        }
    </style>
""", unsafe_allow_html=True)


# Menú lateral
st.sidebar.title("Menu")

# Caja de color en el sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
    box_container = st.container()  # Contenedor para los botones
    with box_container:
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


# Banner superior
banner_text = "CVT Final Processes"
st.markdown(f"<div class='top-banner'>{banner_text}</div>", unsafe_allow_html=True)

# Caja central de color
with st.container():
    st.markdown('<div class="central-box">', unsafe_allow_html=True)
    st.write("Aquí va el contenido principal...")
    st.markdown('</div>', unsafe_allow_html=True)
