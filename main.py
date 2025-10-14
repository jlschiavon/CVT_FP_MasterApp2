import streamlit as st
import pandas as pd
import os
from datetime import datetime
import numpy as np
from datetime import date
import matplotlib.pyplot as plt
from utils.load_clean_alds import cargar_alds
from utils.load_clean_mes import cargar_mes
from utils.load_clean_oee import cargar_oee
from utils.helpers import generar_union_final
from io import BytesIO

print(os.listdir())
print(os.listdir("utils"))


# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")
st.title("Master App CVT Final Processes")

# --- Inicializar estado ---
if 'files' not in st.session_state:
    st.session_state.files = {}
if 'section' not in st.session_state:
    st.session_state.section = 'upload'

# --- Definir archivos esperados ---
expected_files = {
    "OEE": {"keywords": ["SQLReport"], "format": ["xlsx"]},
    "Production": {"keywords": ["05 - Overview", "31 - Overview", "correctionQty", "recken", "vpk"], "format": ["xlsx", "xlsx", "csv"]},
    "Scrap": {"keywords": ["EXPORT", "correctionQty", "recken", "vpk"], "format": ["xls", "xlsx"]},
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

# ================================
# --- SECCIÓN DE CARGA DE ARCHIVOS
# ================================
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
                        # Cargar según extensión
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

# ================================
# --- SECCIÓN OEE
# ================================
from utils.process_oee import procesar_oee

elif st.session_state.section == "OEE":
    st.header("📊 Sección: OEE (Procesamiento de SQLReport)")

    # Buscar archivo
    sql_file = None
    for key in st.session_state.files:
        if "sqlreport" in key.lower():
            sql_file = st.session_state.files[key]
            break

    if sql_file is None:
        st.warning("⚠ No se ha cargado el archivo correspondiente a SQLReport aún.")
    else:
        selected_date = st.date_input("Seleccione la fecha para mostrar OEE (opcional)", value=None)
        procesar_OEE_KPI(sql_file, selected_date)

# ================================
# --- SECCIÓN PRODUCTION
# ================================
# ================================
# --- SECCIÓN PRODUCTION (RECKEN)
# ================================
elif st.session_state.section == "Production":
    st.header("📊 Production - Recken")

    # 1️⃣ Detectar archivos
    recken_alds_df, recken_mes_df, recken_oee_df = None, None, None
    for key, df in st.session_state.files.items():
        lower_key = key.lower()
        if "overview" in lower_key and "05" in lower_key:
            recken_alds_df = df
        elif any(x in lower_key for x in ["correction", "qty", "correctionQty"]):
            recken_mes_df = df
        elif "recken" in lower_key:
            recken_oee_df = df

    # 2️⃣ Mostrar estado
    st.subheader("📦 Archivos Detectados Automáticamente (Recken)")
    st.write(f"ALDS_Recken: {'✅' if recken_alds_df is not None else '❌'}")
    st.write(f"MES_Recken: {'✅' if recken_mes_df is not None else '❌'}")
    st.write(f"OEE_Recken: {'✅' if recken_oee_df is not None else '❌'}")

    if not any([recken_alds_df, recken_mes_df, recken_oee_df]):
        st.warning("⚠ Faltan archivos para iniciar el análisis de Producción Recken.")
        st.stop()

    # 3️⃣ Procesamiento
    st.subheader("⚙ Procesamiento Inicial")
    if st.button("🚀 Process Production Data - Recken"):
        try:
            alds_clean, df_final = procesar_recken(recken_alds_df, recken_mes_df)
        except Exception as e:
            st.error(f"❌ Error procesando Archivos: {e}")
