import streamlit as st
import pandas as pd
import os
from datetime import datetime
import numpy as np
from datetime import date
import matplotlib.pyplot as plt
from utils.load_alds_recken import cargar_alds
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

        # --- Procesamiento fechas ---
        df["Date"] = df["Date"].astype(str)
        df[["YYYY","MM","DD"]] = df["Date"].str.split("-", expand=True)
        df.drop(["Date","Unplanned"], axis=1, inplace=True, errors='ignore')
        for col in ["YYYY","MM","DD"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["YYYY","MM","DD"])
        df[["YYYY","MM","DD"]] = df[["YYYY","MM","DD"]].astype(int)

        # Selector de fecha opcional
        selected_date = st.date_input("Seleccione la fecha para mostrar OEE (opcional)", value=None)

        if selected_date:
            day, month, year = selected_date.day, selected_date.month, selected_date.year
            df_filtered = df[(df["DD"]==day) & (df["MM"]==month) & (df["YYYY"]==year)]
        else:
            df_filtered = df[df["Shift"]=="Daily"]

        # Reemplazo nombres
        machine_map = {
            "83947050 | Bancos de prueba de tensión (7050)(1)": "Recken 7050 (JATCO)",
            "83947150 | Bancos de prueba de tensión (7150) (1)": "Recken 7150 (HYUNDAI)",
            "83947250 | Bancos de prueba de tensión (7250) (1)": "Recken 7250 (GM)",
            "12525645 | Estación de inspección 100% (1)": "VPK 1",
            "12710703 | Estación de inspección 100% (2)": "VPK 2"
        }
        df_filtered["Machine"] = df_filtered["Machine"].replace(machine_map)

        # Colores vs target
        target_recken = 85
        target_vpk = 65
        def color_oee_recken(val):
            if pd.isna(val): return ""
            return "background-color: lightgreen" if target_recken-5 <= val <= target_recken+5 else "background-color: lightcoral"
        def color_oee_vpk(val):
            if pd.isna(val): return ""
            return "background-color: lightgreen" if target_vpk-5 <= val <= target_vpk+5 else "background-color: lightcoral"

        # Mostrar tabla por máquina
        for machine in df_filtered["Machine"].unique():
            st.subheader(f"{machine}" + (f" - Fecha: {day:02d}/{month:02d}/{year}" if selected_date else ""))
            df_machine = df_filtered[df_filtered["Machine"] == machine]
            if "Recken" in machine:
                df_styled = df_machine.style.applymap(color_oee_recken, subset=["Act.-OEE [%]"])
            elif "VPK" in machine:
                df_styled = df_machine.style.applymap(color_oee_vpk, subset=["Act.-OEE [%]"])
            else:
                df_styled = df_machine
            st.dataframe(df_styled, hide_index=True, column_order=("DD","Shift","Act.-OEE [%]","AF [%]","PF [%]","QF [%]"))
    st.markdown("---")  # Separador visual
    st.header("📈 Promedios de Desempeño")
    
    # --- Función OEE fórmula ---
    def calc_oee_formula(df_machine):
        df_shift = df_machine[df_machine["Shift"] != "Daily"].copy()
        if df_shift.empty:
            return None
        cols = [
            "Production min.", "Planned min. (plan. op. time)",
            "Planned min. (Prod. qty.)", "Yield qty.", "Prod. qty."
        ]
        df_shift[cols] = df_shift[cols].fillna(0)
        oee_series = (
            (df_shift["Production min."] / df_shift["Planned min. (plan. op. time)"]) *
            (df_shift["Planned min. (Prod. qty.)"] / df_shift["Production min."]) *
            (df_shift["Yield qty."] / df_shift["Prod. qty."])
        )
        return oee_series.mean() * 100
    
    # --- Máquinas ---
    recken_machines = ["Recken 7050 (JATCO)", "Recken 7150 (HYUNDAI)", "Recken 7250 (GM)"]
    vpk_machines = ["VPK 1", "VPK 2"]
    
    # --- Diccionario de OEE por máquina ---
    oee_dict = {}
    
    if selected_date:  # usuario seleccionó fecha
        for m in recken_machines + vpk_machines:
            # Buscar fila Daily de la fecha seleccionada
            df_daily = df_filtered[
                (df_filtered["Machine"] == m) &
                (df_filtered["Shift"] == "Daily") &
                (df_filtered["DD"] == day) &
                (df_filtered["MM"] == month) &
                (df_filtered["YYYY"] == year)
            ]
            if not df_daily.empty:
                oee_dict[m] = df_daily["Act.-OEE [%]"].values[0]
            else:
                oee_dict[m] = np.nan
    else:  # no hay fecha seleccionada, calcular usando fórmula
        def calc_oee_formula(df_machine):
            df_shift = df_machine[df_machine["Shift"] != "Daily"].copy()
            if df_shift.empty:
                return np.nan
            cols = [
                "Production min.", "Planned min. (plan. op. time)",
                "Planned min. (Prod. qty.)", "Yield qty.", "Prod. qty."
            ]
            df_shift[cols] = df_shift[cols].fillna(0)
            oee_series = (
                (df_shift["Production min."] / df_shift["Planned min. (plan. op. time)"].replace(0, np.nan)) *
                (df_shift["Planned min. (Prod. qty.)"] / df_shift["Production min"].replace(0, np.nan)) *
                (df_shift["Yield qty."] / df_shift["Prod. qty."].replace(0, np.nan))
            )
            return oee_series.mean() * 100
    
        for m in recken_machines + vpk_machines:
            oee_dict[m] = calc_oee_formula(df_filtered[df_filtered["Machine"] == m])
    
    # --- Calcular OEE global ---
    def calc_global(oee_list):
        valid_vals = [v for v in oee_list if not np.isnan(v)]
        if not valid_vals:
            return np.nan
        return np.mean(valid_vals)
    
    oee_global_recken = calc_global([oee_dict[m] for m in recken_machines])
    oee_global_vpk = calc_global([oee_dict[m] for m in vpk_machines])
    
    # --- Mostrar tarjetas por máquina ---
    st.markdown("### 🏭 OEE por Máquina")
    machine_cols = st.columns(len(oee_dict))
    for idx, (machine, val) in enumerate(oee_dict.items()):
        # Definir color de manera segura
        if val is None or np.isnan(val):
            color = "red"
        else:
            if "Recken" in machine:
                color = "green" if (target_recken - 5 <= val <= target_recken + 5) else "red"
            elif "VPK" in machine:
                color = "green" if (target_vpk - 5 <= val <= target_vpk + 5) else "red"
            else:
                color = "red"
    
        display_val = 0 if val is None or np.isnan(val) else val
    
        with machine_cols[idx]:
            st.markdown(f"""
            <div style='background-color:#f7f5f5; padding:15px; border-radius:10px; border:8px solid {color}; text-align:center'>
                <h5 style='color:black'>{machine}</h5>
                <h3 style='color:black'>{display_val:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)
    
    # --- Tarjetas globales ---
    st.markdown("### 📊 OEE Global por Grupo")
    cols = st.columns(2)
    with cols[0]:
        color = "green" if not np.isnan(oee_global_recken) and (target_recken - 5 <= oee_global_recken <= target_recken + 5) else "red"
        display_val = 0 if np.isnan(oee_global_recken) else oee_global_recken
        st.markdown(f"""
        <div style='background-color:#f7f5f5; padding:20px; border-radius:10px; border:8px solid {color}; text-align:center'>
            <h4 style='color:black'>Recken Global</h4>
            <h2 style='color:black'>{display_val:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        color = "green" if not np.isnan(oee_global_vpk) and (target_vpk - 5 <= oee_global_vpk <= target_vpk + 5) else "red"
        display_val = 0 if np.isnan(oee_global_vpk) else oee_global_vpk
        st.markdown(f"""
        <div style='background-color:#f7f5f5; padding:20px; border-radius:10px; border:8px solid {color}; text-align:center'>
            <h4 style='color:black'>VPK Global</h4>
            <h2 style='color:black'>{display_val:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    #------------- GRÁFICAS
    
    st.markdown("---")  # Separador visual
    st.header("📊 Gráficas de OEE")
    
    # Gráficas Recken
    st.subheader("📊 Gráficas OEE - Recken")
    recken_machines = ["Recken 7050 (JATCO)", "Recken 7150 (HYUNDAI)", "Recken 7250 (GM)"]
    df_plot = df_filtered[df_filtered["Machine"].isin(recken_machines) & (df_filtered["Shift"]=="Daily")].copy()
    
    if not df_plot.empty:
        plt.figure(figsize=(12,4))
        colors = {
            "Recken 7050 (JATCO)":"#004A30",
            "Recken 7150 (HYUNDAI)":"#003984",
            "Recken 7250 (GM)":"#0671D8"
        }
    
        for machine in recken_machines:
            df_m = df_plot[df_plot["Machine"]==machine]
            plt.bar(
                df_m["DD"] + recken_machines.index(machine)*0.2,
                df_m["Act.-OEE [%]"],
                width=0.2,
                color=colors[machine],
                label=machine,
                edgecolor='black'
            )
    
        plt.axhline(y=target_recken, color='red', linestyle='--', linewidth=2, label=f'Target {target_recken}%')
        plt.xticks(range(1,32))
        plt.yticks(range(0,125,5))
        plt.ylim(0,120)
        plt.xlabel("Día del mes")
        plt.ylabel("OEE [%]")
        plt.title("Evolución diaria de OEE - Máquinas Recken")
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=len(recken_machines)+1, fontsize=10)
        st.pyplot(plt.gcf())
        plt.clf()
    else:
        st.warning("No hay datos disponibles para las máquinas Recken")
    
    #------------- GRÁFICAS VPK
    st.header("📊 Gráficas OEE - VPK")
    vpk_machines = ["VPK 1", "VPK 2"]
    df_plot_vpk = df_filtered[(df_filtered["Machine"].isin(vpk_machines)) & (df_filtered["Shift"] == "Daily")].copy()
    
    if not df_plot_vpk.empty:
        plt.figure(figsize=(12,4))  # menos alto para visual más compacto
        
        # Colores distintos para cada máquina VPK
        colors_vpk = {
            "VPK 1": "#9C27B0",  # morado
            "VPK 2": "#FF5722"   # naranja rojizo
        }
        
        # Agrupar por máquina
        for machine in vpk_machines:
            df_machine = df_plot_vpk[df_plot_vpk["Machine"] == machine]
            plt.bar(
                df_machine["DD"] + vpk_machines.index(machine)*0.2,  # desplazamiento para evitar superposición
                df_machine["Act.-OEE [%]"],
                width=0.2,
                color=colors_vpk[machine],
                label=machine,
                edgecolor='black'
            )
        
        # Línea del target
        plt.axhline(y=target_vpk, color='red', linestyle='--', linewidth=2, label=f'Target {target_vpk}%')
        
        # Configuración de ejes
        plt.xticks(range(1,32))  # días del mes
        plt.yticks(range(0, 125, 5))
        plt.ylim(0, 120)
        plt.xlabel("Día del mes")
        plt.ylabel("OEE [%]")
        plt.title("Evolución diaria de OEE - Máquinas VPK")
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Leyenda horizontal abajo, más pequeña
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=len(vpk_machines)+1, fontsize=10)
        
        st.pyplot(plt.gcf())
        plt.clf()
    else:
        st.warning("No hay datos disponibles para las máquinas VPK")

# ================================
# --- SECCIÓN PRODUCTION
# ================================
# ================================
# --- SECCIÓN PRODUCTION (RECKEN)
# ================================
elif st.session_state.section == "Production":
    st.header("📊 Production - Recken")

    # -------------------------------------------
    # 1️⃣ DETECCIÓN DE ARCHIVOS RELEVANTES
    # -------------------------------------------
    recken_alds_df = None
    recken_mes_df = None
    recken_oee_df = None

    for key, df in st.session_state.files.items():
        lower_key = key.lower()

        # ALDS (Overview archivos tipo 05 o 31)
        if "overview" in lower_key:
            if "05" in lower_key:
                recken_alds_df = df

        # MES (Otros "Overview")
        elif "correctionQty" in lower_key:
            recken_mes_df = df

        # OEE (SQLReport o Recken)
        elif "recken" in lower_key:
            recken_oee_df = df

    # -------------------------------------------
    # 2️⃣ VISUALIZAR EL ESTADO DE ARCHIVOS
    # -------------------------------------------
    st.subheader("📦 Archivos Detectados Automáticamente (Recken)")
    st.write(f"ALDS_Recken: {'✅' if recken_alds_df is not None else '❌'}")
    st.write(f"MES_Recken: {'✅' if recken_mes_df is not None else '❌'}")
    st.write(f"OEE_Recken: {'✅' if recken_oee_df is not None else '❌'}")

    if not any([recken_alds_df is not None, recken_mes_df is not None, recken_oee_df is not None]):
        st.warning("⚠ Faltan archivos para iniciar el análisis de Producción Recken.")
        st.stop()
    else:
        st.success("✅ Archivos listos para procesar Producción Recken")

    # -------------------------------------------
    # 3️⃣ BOTÓN DE PROCESAMIENTO CENTRAL
    # -------------------------------------------
    st.subheader("⚙ Procesamiento Inicial")

    if st.button("🚀 Process Production Data - Recken"):
        try:
            recken_alds_clean = cargar_alds({"05 - Overview": recken_alds_df})

            if recken_alds_clean is None or recken_alds_clean.empty:
                st.error("❌ Error: cargar_alds no devolvió datos válidos para Recken.")
            else:
                st.success("✅ ALDS_Recken generado correctamente")
                st.dataframe(recken_alds_clean, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error procesando ALDS_Recken: {e}")
