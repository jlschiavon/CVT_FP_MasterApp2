import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# --- Inicializar estado ---
if 'files' not in st.session_state:
    st.session_state.files = {}
if 'section' not in st.session_state:
    st.session_state.section = 'upload'

# --- Definir archivos esperados ---
expected_files = {
    "OEE": {"keywords": ["SQLReport","recken", "vpk"], "format": ["xls", "xlsx", "csv"]},
    "Production": {"keywords": ["correctionQty", "05 - Overview", "31 - Overview", "EXPORT"], "format": ["xls", "xlsx"]},
    "Scrap": {"keywords": ["EXPORT"], "format": ["xls", "xlsx"]},
    "Paros": {"keywords": ["n2", "n3"], "format": ["txt"]},
    "Oil Tracking": {"keywords": ["Tracking Consumo de ATF"], "format": ["xls", "xlsx"]},
    "Negative": {"keywords": ["neg"], "format": ["xls", "xlsx"]}
}

# --- Sidebar ---
st.sidebar.title("Menu")
if st.sidebar.button("📂 Cargar Archivos"):
    st.session_state.section = "upload"

# Habilitar botones según archivos cargados
for section_name, info in expected_files.items():
    if any(k in st.session_state.files for k in info['keywords']):
        if st.sidebar.button(section_name):
            st.session_state.section = section_name

# --- Sección de carga de archivos ---
if st.session_state.section == "upload":
    st.header("📂 Cargar Archivos CSV/XLS/TXT")
    uploaded_files = st.file_uploader(
        "Selecciona uno o varios archivos",
        type=["csv", "xlsx", "xls", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            file_name = file.name.lower()
            matched = False
            for sect, info in expected_files.items():
                for kw in info['keywords']:
                    if kw.lower() in file_name:
                        if file.name.endswith(".csv") or file.name.endswith(".txt"):
                            df = pd.read_csv(file)
                        else:
                            df = pd.read_excel(file)
                        st.session_state.files[kw] = df
                        matched = True
            if matched:
                st.success(f"Archivo '{file.name}' cargado correctamente ✅")
            else:
                st.warning(f"Archivo '{file.name}' no coincide con ningún reporte esperado ⚠")

    # Estado de archivos cargados
    st.subheader("Archivos cargados actualmente:")
    for sect, info in expected_files.items():
        status = "❌"
        for kw in info['keywords']:
            if kw in st.session_state.files:
                status = "✅"
                break
        st.write(f"{sect}: {status}")

# --- Sección específica: OEE ---
elif st.session_state.section == "OEE":
    st.header("📊 Sección: OEE (Procesamiento de SQLReport)")

    # Buscar archivo SQLReport
    sql_file = None
    for key in st.session_state.files:
        if "sqlreport" in key.lower():
            sql_file = st.session_state.files[key]
            break

    if sql_file is None:
        st.warning("⚠ No se ha cargado el archivo correspondiente a SQLReport aún.")
    else:
        df = sql_file.copy()

        # 1. Añadir columnas YYYY, MM, DD
        date_col_index = df.columns.get_loc("Date") + 1
        df.insert(date_col_index, "YYYY", "")
        df.insert(date_col_index + 1, "MM", "")
        df.insert(date_col_index + 2, "DD", "")

        # 2. Dividir Date
        date_split = df["Date"].astype(str).str.split("-", expand=True)
        df["YYYY"] = date_split[0]
        df["MM"] = date_split[1]
        df["DD"] = date_split[2]
        df.drop(["Date","Unplanned"], axis=1, inplace=True)
        # Convertir columna DD, MM, YYYY a tipo entero para comparación
        df["DD"] = df["DD"].astype(int)
        df["MM"] = df["MM"].astype(int)
        df["YYYY"] = df["YYYY"].astype(int)

        # --- Selector de fecha ---
        selected_date = st.date_input(
            "Seleccione la fecha para mostrar OEE",
            value=pd.to_datetime("today")
        )

        # Extraer día, mes, año de la fecha seleccionada
        day = selected_date.day
        month = selected_date.month
        year = selected_date.year
        
        # --- Filtrado ---
        # Si el usuario no toca el selector (fecha hoy) se mantiene Daily
        # Si selecciona otra fecha, filtramos todas las filas de esa fecha independientemente del Shift
        if selected_date == pd.to_datetime("today"):
            df_filtered = df[df["Shift"] == "Daily"]
        else:
            df_filtered = df[
                (df["DD"] == day) &
                (df["MM"] == month) &
                (df["YYYY"] == year)
            ]

        # 3. Filtrar solo "Daily"
        df = df[df["Shift"] == "Daily"]

        # 4. Reemplazar nombres de Machine
        machine_map = {
            "83947050 | Bancos de prueba de tensión (7050)(1)": "Recken 7050 (JATCO)",
            "83947150 | Bancos de prueba de tensión (7150) (1)": "Recken 7150 (HYUNDAI)",
            "83947250 | Bancos de prueba de tensión (7250) (1)": "Recken 7250 (GM)",
            "12525645 | Estación de inspección 100% (1)": "VPK 1",
            "12710703 | Estación de inspección 100% (2)": "VPK 2"
        }
        df["Machine"] = df["Machine"].replace(machine_map)

        # Mostrar todos los DataFrames de cada máquina con scroll
        for machine in df["Machine"].unique():
            st.subheader(f"{machine} - Fecha: {day:02d}/{month:02d}/{year}")
            st.dataframe(df[df["Machine"] == machine], hide_index=1, column_order=("DD","Shift","Act.-OEE [%]","AF [%]","PF [%]","QF [%]"))

# --- Secciones genéricas ---
elif st.session_state.section in expected_files:
    st.header(f"📊 Sección: {st.session_state.section}")

    # Mostrar el primer archivo cargado completo
    for kw in expected_files[st.session_state.section]["keywords"]:
        if kw in st.session_state.files:
            st.dataframe(st.session_state.files[kw])
            break
