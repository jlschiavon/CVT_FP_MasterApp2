import streamlit as st

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
        /* Fondo de la página */
        div[data-testid="stAppViewContainer"] {
            background-color: #626262; /* gris */
        }

        /* Panel lateral */
        section[data-testid="stSidebar"] {
            background-color: #D9D9D9; 
            padding: 10px;
            border-radius: 20px;
            text-align: center;
        }

        /* Caja interna en el panel central */
        .central-box {
            background-color: #D9D9D9; 
            padding: 20px;
            border-radius: 15px;
            margin-top: 10px;
        }
        
        /* Caja interna en el sidebar */
        .sidebar-box {
            background-color: #626262; 
            padding: 15px;
            border-radius: 12px;
            margin-top: 20px;
        }

        /* Rectángulo superior (banner) */
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

# Menú lateral con caja
st.sidebar.title("Menú")
with st.sidebar.container():
    st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)

    if st.button("OEE", key="btn1"):
        st.session_state.section = "OEE"
    if st.button("Producción", key="btn2"):
        st.session_state.section = "Production"
    if st.button("Scrap", key="btn3"):
        st.session_state.section = "Scrap"
    if st.button("Paros de máquina", key="btn4"):
        st.session_state.section = "Machine Breakdowns"
    if st.button("Aceite ATF", key="btn5"):
        st.session_state.section = "Oil Tracking"
    if st.button("Negativo", key="btn6"):
        st.session_state.section = "Negative"

    st.markdown('</div>', unsafe_allow_html=True)

# Banner superior
banner_text = "CVT Final Processes"
st.markdown(f"<div class='top-banner'>{banner_text}</div>", unsafe_allow_html=True)

# Caja en el panel central
with st.container():
    st.markdown('<div class="central-box">', unsafe_allow_html=True)
    st.write("📊 Aquí va el contenido dinámico del panel central.")
    st.markdown('</div>', unsafe_allow_html=True)
