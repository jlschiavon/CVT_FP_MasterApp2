import streamlit as st
import pandas as pd
import io
import re


# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# --- Inicializar estado ---
if 'files' not in st.session_state:
    st.session_state.files = {}
if 'section' not in st.session_state:
    st.session_state.section = 'upload'

# --- Definir archivos esperados ---
expected_files = {
    "OEE": {"keywords": ["SQLReport", "recken", "vpk"], "format": ["xls", "xlsx", "csv"]},
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


# ---- Sección OEE robusta ----
elif section == "OEE":
    st.header("📊 Sección: OEE (Procesamiento de SQLReport)")

    # 1) Buscar el archivo SQLReport de forma flexible: por nombre o por contenido (columnas)
    sql_df = None
    sql_key = None

    # Primero intenta por nombre de clave/file name que contenga 'sqlreport'
    for key, val in st.session_state.files.items():
        try:
            name = str(key)
        except:
            name = ""
        if "sqlreport" in name.lower():
            sql_df = val.copy()
            sql_key = key
            break

    # Si no lo encontramos por nombre, buscamos un dataframe que tenga columnas 'date' y 'machine'
    if sql_df is None:
        for key, val in st.session_state.files.items():
            df_try = val.copy()
            cols_norm = [str(c).strip().lower() for c in df_try.columns]
            if any("machine" in c for c in cols_norm) and any("date" in c for c in cols_norm):
                sql_df = df_try.copy()
                sql_key = key
                break

    if sql_df is None:
        st.warning("No se encontró un archivo SQLReport. Sube el archivo (xls/xlsx/csv/txt) o verifica el nombre.")
    else:
        df = sql_df.copy()

        # util: encontrar columna por token parcial (case-insensitive)
        def find_col(df, token):
            token = token.lower()
            for col in df.columns:
                if token in str(col).strip().lower():
                    return col
            return None

        date_col = find_col(df, "date")
        machine_col = find_col(df, "machine")
        shift_col = find_col(df, "shift")

        if date_col is None or machine_col is None or shift_col is None:
            st.error("No se detectaron columnas 'Date', 'Machine' o 'Shift'. Columnas encontradas:\n" + ", ".join(map(str, df.columns)))
            st.dataframe(df.head())
        else:
            # 1) Insertar YYYY, MM, DD justo después de Date (si no existen)
            cols = list(df.columns)
            date_idx = cols.index(date_col) + 1
            for newcol in ["YYYY", "MM", "DD"]:
                if newcol not in df.columns:
                    df.insert(date_idx, newcol, "")
                    date_idx += 1

            # 2) Split Date por '-' (fallback a parseo si no tiene '-')
            date_series = df[date_col].astype(str).str.strip()
            parts = date_series.str.split("-", expand=True)
            if parts.shape[1] >= 3:
                df["YYYY"] = parts[0]
                df["MM"]  = parts[1]
                df["DD"]  = parts[2]
            else:
                # fallback: usar to_datetime y extraer
                parsed = pd.to_datetime(date_series, errors="coerce", dayfirst=False)
                df["YYYY"] = parsed.dt.year.astype("Int64").astype(str)
                df["MM"]  = parsed.dt.month.astype("Int64").astype(str).str.zfill(2)
                df["DD"]  = parsed.dt.day.astype("Int64").astype(str).str.zfill(2)

            # 3) Filtrar solo filas con Shift == "Daily" (limpiando espacios y case)
            df = df[df[shift_col].astype(str).str.strip().str.lower() == "daily"].copy()

            # 4) Reemplazo de Machine usando coincidencias parciales (más flexible)
            machine_patterns = {
                "Recken 7050 (JATCO)": ["83947050", "7050", "bancos de prueba", "7050)"],
                "Recken 7150 (HYUNDAI)": ["83947150", "7150", "7150)"],
                "Recken 7250 (GM)": ["83947250", "7250"],
                "VPK 1": ["12525645", "estación de inspección 100% (1)", "estacion de inspeccion 100% (1)"],
                "VPK 2": ["12710703", "estación de inspección 100% (2)", "estacion de inspeccion 100% (2)"]
            }

            def map_machine(val):
                s = str(val).lower()
                for new_name, patterns in machine_patterns.items():
                    for p in patterns:
                        if p.lower() in s:
                            return new_name
                return val  # si no coincide, conservar original

            df[machine_col] = df[machine_col].apply(map_machine)

            # Mostrar la tabla final procesada
            st.subheader("✅ Tabla OEE procesada (filtrada y renombrada):")
            st.dataframe(df, use_container_width=True)

            # Ofrecer descarga del CSV procesado
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Descargar OEE procesado (CSV)", data=csv_bytes, file_name="OEE_processed.csv", mime="text/csv")

            st.info(f"Archivo usado: {sql_key}")
