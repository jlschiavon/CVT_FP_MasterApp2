import streamlit as st

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# CSS
st.markdown("""
    <style>
        /* Fondo del área central */
        div[data-testid="stAppViewContainer"] {
            background-color: #626262;
        }

        /* Fondo del sidebar */
        section[data-testid="stSidebar"] {
            background-color: #D9D9D9;
            padding: 10px;
            border-radius: 20px;
        }

        /* Caja del menú lateral */
        div[data-testid="sidebar-box"] {
            background-color: #626262;
            padding: 15px;
            border-radius: 12px;
            margin-top: 20px;
        }

        /* Caja central */
        div[data-testid="central-box"] {
            background-color: #D9D9D9;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
        }

        /* Banner superior */
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

        st.markdown("""
    <style>
        ...

        /* Caja del menú lateral */
        div[data-testid="sidebar-box"] {
            background-color: #626262;
            padding: 15px;
            border-radius: 12px;
            margin-top: 20px;
            text-align: center; /* 👈 NUEVO */
        }

        /* Botones */
        .stButton>button {
            display: block;
            width: 80% !important;  /* 👈 Cambiado de 100% a 80% */
            margin: 0 auto;         /* 👈 Centrado horizontal */
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

        .stButton>button:hover {
            background-color: #2d8c20;
        }
    </style>
""", unsafe_allow_html=True)


# Menú lateral con caja
st.sidebar.title("Menu")

with st.sidebar:
    st.markdown('<div data-testid="sidebar-box">', unsafe_allow_html=True)

    if st.button("OEE", key="oee"):
        st.session_state.section = "OEE"
    if st.button("Producción", key="prod"):
        st.session_state.section = "Production"
    if st.button("Scrap", key="scrap"):
        st.session_state.section = "Scrap"
    if st.button("Paros de máquina", key="paros"):
        st.session_state.section = "Machine Breakdowns"
    if st.button("Oil Tracking ATF", key="oil"):
        st.session_state.section = "Oil Tracking"
    if st.button("Negative", key="neg"):
        st.session_state.section = "Negative"

        st.markdown('</div>', unsafe_allow_html=True)


# Banner superior
st.markdown(f"<div class='top-banner'>CVT Final Processes</div>", unsafe_allow_html=True)

# Caja central
with st.container():
    st.markdown('<div data-testid="central-box">', unsafe_allow_html=True)
    st.write("Aquí va el contenido principal...")
    st.markdown('</div>', unsafe_allow_html=True)
