import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="CVT Final Processes", layout="wide")

# --- Inicializar estado ---
if 'files' not in st.session_state:
    st.session_state.files = {}
if 'section' not in st.session_state:
    st.session_state.section = 'upload'

# --- Definir archivos esperados ---
expected_files = {
    "OEE": {"keywords": ["sqlreport","recken", "vpk"], "format": ["xls", "xlsx", "csv"]},
    "Production": {"keywords": ["recken"], "format": ["xls", "xlsx"]},
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

        # Gráficas Recken
        st.header("📊 Gráficas OEE - Recken")
        recken_machines = ["Recken 7050 (JATCO)", "Recken 7150 (HYUNDAI)", "Recken 7250 (GM)"]
        df_plot = df_filtered[df_filtered["Machine"].isin(recken_machines) & (df_filtered["Shift"]=="Daily")].copy()
        if not df_plot.empty:
            plt.figure(figsize=(12,4))
            colors = {"Recken 7050 (JATCO)":"#004A30","Recken 7150 (HYUNDAI)":"#003984","Recken 7250 (GM)":"#0671D8"}
            for machine in recken_machines:
                df_m = df_plot[df_plot["Machine"]==machine]
                plt.bar(df_m["DD"]+recken_machines.index(machine)*0.2, df_m["Act.-OEE [%]"], width=0.2, color=colors[machine], label=machine, edgecolor='black')
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

# ================================
# --- SECCIÓN PRODUCTION
# ================================
elif st.session_state.section == "Production":
    st.header("📊 Production - Reckens")
    
    # Buscar archivo Reckens
    recken_file = None
    for key in st.session_state.files:
        if "recken" in key.lower():
            recken_file = st.session_state.files[key]
            break

    if recken_file is None:
        st.warning("⚠ No se ha cargado el archivo correspondiente a Reckens aún.")
    else:
        df_recken = recken_file.copy()

        # --- Ingreso de chatarra física ---
        st.sidebar.header("Ingreso de chatarra física - Reckens")
        turnos = ["1st Shift", "2nd Shift", "3rd Shift"]
        partes = ["L-0G005-1036-17", "L-0G005-0095-41", "L-0G005-1015-05", "L-0G005-1043-12"]

        if "scrap_fisico_df" not in st.session_state:
            st.session_state.scrap_fisico_df = {(s,p):0 for s in turnos for p in partes}

        for turno in turnos:
            st.sidebar.subheader(turno)
            for i, parte in enumerate(partes):
                orden_key = f"{i:02d}_{turno}_{parte}"
                st.session_state.scrap_fisico_df[(turno, parte)] = st.sidebar.number_input(
                    f"{parte}", min_value=0, step=1, key=orden_key, value=st.session_state.scrap_fisico_df[(turno, parte)]
                )

        if st.sidebar.button("Procesar Reckens"):
            scrap_fisico_df_series = pd.Series({(s,p):v for (s,p),v in st.session_state.scrap_fisico_df.items()})
            scrap_fisico_df = scrap_fisico_df_series.reset_index()
            scrap_fisico_df.columns = ["Shift","Parte","Fisico"]

            df_recken_final = pd.merge(df_recken, scrap_fisico_df, on=["Shift","Parte"], how="left")
            df_recken_final["Parte"] = pd.Categorical(df_recken_final["Parte"], categories=partes, ordered=True)
            df_recken_final = df_recken_final.sort_values(by=["Shift","Parte"])

            st.dataframe(df_recken_final, use_container_width=True)

            # Exportar Excel
            output_path = "recken_final.xlsx"
            df_recken_final.to_excel(output_path, index=False)
            with open(output_path, "rb") as f:
                st.download_button("Descargar Excel - Reckens", f, file_name="recken_final.xlsx")
