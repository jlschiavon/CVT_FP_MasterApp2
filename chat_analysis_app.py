import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# --- Inicializar estado ---
if 'files' not in st.session_state:
    st.session_state.files = {}
if 'section' not in st.session_state:
    st.session_state.section = 'upload'

# --- Definir archivos esperados ---
expected_files = {
    "OEE": {"keywords": ["SQLReport", "recken", "vpk"], "format": ["xls", "xlsx"]},
    "Production": {"keywords": ["correctionQty", "05 - Overview", "31 - Overview", "EXPORT"], "format": ["xls", "xlsx"]},
    "Scrap": {"keywords": ["EXPORT"], "format": ["xls", "xlsx"]},
    "Paros": {"keywords": ["n2", "n3"], "format": ["txt"]},
    "Oil Tracking": {"keywords": ["Tracking Consumo de ATF"], "format": ["xls", "xlsx"]},
    "Negative": {"keywords": ["neg"], "format": ["xls", "xlsx"]}
}

# --- Sidebar con menú dinámico ---
st.sidebar.title("Menu")
if st.sidebar.button("📂 Cargar Archivos"):
    st.session_state.section = "upload"

# Habilitar botones según archivos cargados
for section_name, info in expected_files.items():
    # Activa si al menos un archivo correspondiente está cargado
    if any(k in st.session_state.files for k in info['keywords']):
        if st.sidebar.button(section_name):
            st.session_state.section = section_name

# --- Pantalla principal ---
section = st.session_state.section

if section == "upload":
    st.header("📂 Cargar Archivos CSV/XLS/TXT")
    uploaded_files = st.file_uploader(
        "Selecciona uno o varios archivos",
        type=["csv", "xlsx", "xls", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            file_name = file.name.lower()
            # Detectar tipo y clasificar por palabra clave
            matched = False
            for sect, info in expected_files.items():
                for kw in info['keywords']:
                    if kw.lower() in file_name:
                        # Leer archivo según tipo
                        if file.name.endswith(".csv") or file.name.endswith(".txt"):
                            df = pd.read_csv(file)  
                        else:  # xls / xlsx
                            df = pd.read_excel(file)
                        st.session_state.files[kw] = df
                        matched = True
            if matched:
                st.success(f"Archivo '{file.name}' cargado correctamente ✅")
            else:
                st.warning(f"Archivo '{file.name}' no coincide con ningún reporte esperado ⚠")

    # Mostrar estado de archivos cargados
    st.subheader("Archivos cargados actualmente:")
    for sect, info in expected_files.items():
        status = "❌"
        for kw in info['keywords']:
            if kw in st.session_state.files:
                status = "✅"
                break
        st.write(f"{sect}: {status}")

# --- Ejemplo de análisis según sección ---
elif section in expected_files:
    st.header(f"📊 Sección: {section}")
    # Mostrar el primer archivo cargado que corresponda a la sección
    for kw in expected_files[section]["keywords"]:
        if kw in st.session_state.files:
            st.write(st.session_state.files[kw].head())
            break
    else:
        st.warning("No se han cargado archivos para esta sección aún.")
