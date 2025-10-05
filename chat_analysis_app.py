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
        
# Convertir columnas a enteros de forma segura
df["DD"] = pd.to_numeric(df["DD"], errors="coerce")
df["MM"] = pd.to_numeric(df["MM"], errors="coerce")
df["YYYY"] = pd.to_numeric(df["YYYY"], errors="coerce")
df = df.dropna(subset=["DD", "MM", "YYYY"])
df["DD"] = df["DD"].astype(int)
df["MM"] = df["MM"].astype(int)
df["YYYY"] = df["YYYY"].astype(int)

# --- Selector de fecha ---
selected_date = st.date_input(
    "Seleccione la fecha para mostrar OEE (opcional)",
    value=None  # No seleccionar fecha por defecto
)

# --- Filtrado según selección ---
if selected_date:
    # Si el usuario selecciona fecha: mostrar todas las filas de esa fecha, sin filtro Daily
    day = selected_date.day
    month = selected_date.month
    year = selected_date.year
    df_filtered = df[
        (df["DD"] == day) &
        (df["MM"] == month) &
        (df["YYYY"] == year)
    ]
else:
    # Si no selecciona fecha: mostrar toda la tabla tal como estaba
    df_filtered=df[df["Shift"]=="Daily"]


# 4. Reemplazar nombres de Machine
machine_map = {
    "83947050 | Bancos de prueba de tensión (7050)(1)": "Recken 7050 (JATCO)",
    "83947150 | Bancos de prueba de tensión (7150) (1)": "Recken 7150 (HYUNDAI)",
    "83947250 | Bancos de prueba de tensión (7250) (1)": "Recken 7250 (GM)",
    "12525645 | Estación de inspección 100% (1)": "VPK 1",
    "12710703 | Estación de inspección 100% (2)": "VPK 2"
    }
        
df_filtered["Machine"] = df_filtered["Machine"].replace(machine_map)

# función de colores vs target
target_recken = 85
target_vpk = 65

def color_oee_recken(val):
    if pd.isna(val):
        return ""
    elif val < (target_recken - 5) or val > (target_recken + 5):
        return "background-color: lightcoral"
    else: 
        return "background-color: lightgreen" 
            
def color_oee_vpk(val):
    if pd.isna(val):
        return ""
    elif val < (target_vpk - 5) or val > (target_vpk + 5):
        return "background-color: lightcoral"
    else: 
        return "background-color: lightgreen"

# --- Mostrar tabla por máquina con colores según target ---
for machine in df_filtered["Machine"].unique():
    st.subheader(f"{machine}" + (f" - Fecha: {day:02d}/{month:02d}/{year}" if selected_date else ""))

    # Seleccionar DataFrame de la máquina
    df_machine = df_filtered[df_filtered["Machine"] == machine]

    # Determinar la función de color según el tipo de máquina
    if "Recken" in machine:
        df_styled = df_machine.style.applymap(color_oee_recken, subset=["Act.-OEE [%]"])
    elif "VPK" in machine:
        df_styled = df_machine.style.applymap(color_oee_vpk, subset=["Act.-OEE [%]"])
    else:
        df_styled = df_machine  # Si es otro tipo de máquina, sin coloreado

    # Mostrar la tabla en Streamlit
    st.dataframe(df_styled, hide_index=True, column_order=("DD","Shift","Act.-OEE [%]","AF [%]","PF [%]","QF [%]"))

st.markdown("---")  # Separador visual

st.header("📈 Promedios de Desempeño")

# --- Función para calcular OEE ---
def calc_oee(df_machine):
    # Filtrar registros donde Shift != "Daily"
    df_shift = df_machine[df_machine["Shift"] != "Daily"]
    if df_shift.empty:
        return None
    # Fórmula OEE: (Production min / Planned min plan op) * (Planned min Prod qty / Production min) * (Yield qty / Prod qty)
    oee_series = (
        (df_shift["Production min."] / df_shift["Planned min. (plan. op. time)"]) *
        (df_shift["Planned min. (Prod. qty.)"] / df_shift["Production min."]) *
        (df_shift["Yield qty."] / df_shift["Prod. qty."])
    )
    # Retornar promedio en porcentaje
    return oee_series.mean() * 100

# --- Agrupar máquinas ---
recken_machines = ["Recken 7050 (JATCO)", "Recken 7150 (HYUNDAI)", "Recken 7250 (GM)"]
vpk_machines = ["VPK 1", "VPK 2"]

# --- Calcular OEE por máquina ---
oee_dict = {}
for m in recken_machines + vpk_machines:
    oee_val = calc_oee(df_filtered[df_filtered["Machine"] == m])
    if oee_val is not None:
        oee_dict[m] = oee_val

# --- Calcular OEE global ---
oee_global_recken = np.mean([oee_dict[m] for m in recken_machines if m in oee_dict])
oee_global_vpk = np.mean([oee_dict[m] for m in vpk_machines if m in oee_dict])

# --- Mostrar tarjetas ---
st.markdown("### 📊 OEE Global por Grupo")
cols = st.columns(2)

with cols[0]:
    color = "green" if oee_global_recken < (target_recken - 4) or oee_global_recken > (target_recken + 4) else "red"
    st.markdown(f"""
    <div style='background-color:#c4c4c4; padding:20px; border-radius:10px; border:8px solid {color}; text-align:center'>
        <h4 style='color:white'>Recken Global</h4>
        <h2 style='color:white'>{oee_global_recken:.1f}%</h2>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    color = "green" if oee_global_vpk >= target_vpk else "red"
    st.markdown(f"""
    <div style='background-color:#1e1e1e; padding:20px; border-radius:10px; border:3px solid {color}; text-align:center'>
        <h4 style='color:white'>VPK Global</h4>
        <h2 style='color:white'>{oee_global_vpk:.1f}%</h2>
    </div>
    """, unsafe_allow_html=True)

# --- Mostrar OEE por máquina ---
st.markdown("### 🏭 OEE por Máquina")
machine_cols = st.columns(len(oee_dict))
for idx, (machine, val) in enumerate(oee_dict.items()):
    color = "green" if ("Recken" in machine and val >= target_recken) or ("VPK" in machine and val >= target_vpk) else "red"
    with machine_cols[idx]:
        st.markdown(f"""
        <div style='background-color:#1e1e1e; padding:15px; border-radius:10px; border:3px solid {color}; text-align:center'>
            <h5 style='color:white'>{machine}</h5>
            <h3 style='color:white'>{val:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)

