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

elif section == "OEE":
    st.header("📊 Sección: OEE (Procesamiento de SQLReport)")

    # Buscar archivo con keyword SQLReport
    sql_file = None
    for key in st.session_state.files:
        if "sqlreport" in key.lower():
            sql_file = st.session_state.files[key]
            break

    if sql_file is None:
        st.warning("⚠ No se ha cargado el archivo correspondiente a SQLReport aún.")
    else:
        df = sql_file.copy()

        # 1. Añadir 3 columnas vacías después de "Date"
        date_col_index = df.columns.get_loc("Date") + 1
        df.insert(date_col_index, "YYYY", "")
        df.insert(date_col_index + 1, "MM", "")
        df.insert(date_col_index + 2, "DD", "")

        # 2. Dividir la columna Date usando "-" en YYYY, MM, DD
        date_split = df["Date"].astype(str).str.split("-", expand=True)
        df["YYYY"] = date_split[0]
        df["MM"] = date_split[1]
        df["DD"] = date_split[2]

        # 3. Filtrar solo filas con Shift "Daily" (limpiando espacios y upper/lower)
        df = df[df["Shift"].astype(str).str.strip().str.lower() == "daily"]

        # 4. Reemplazar nombres en Machine con coincidencias parciales
        replacements = {
            "7050": "Recken 7050 (JATCO)",
            "7150": "Recken 7150 (HYUNDAI)",
            "7250": "Recken 7250 (GM)",
            "estación de inspección 100% (1)": "VPK 1",
            "estación de inspección 100% (2)": "VPK 2"
        }

        def replace_machine(value):
            val = value.lower()
            for key, new_name in replacements.items():
                if key in val:  # coincidencia parcial
                    return new_name
            return value  # si no coincide lo dejamos igual

        df["Machine"] = df["Machine"].astype(str).apply(replace_machine)

        # Mostrar tabla final procesada
        st.subheader("✅ Tabla después de aplicar filtros y reemplazos:")
        st.dataframe(df, use_container_width=True)
