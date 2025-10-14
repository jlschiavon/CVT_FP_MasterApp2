import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

def procesar_oee(sql_df, selected_date=None):
    """
    Procesa el archivo SQLReport y genera tablas, KPIs y gráficas de OEE.
    """

    # --- Procesamiento fechas ---
    df = sql_df.copy()
    df["Date"] = df["Date"].astype(str)
    df[["YYYY","MM","DD"]] = df["Date"].str.split("-", expand=True)
    df.drop(["Date","Unplanned"], axis=1, inplace=True, errors='ignore')
    for col in ["YYYY","MM","DD"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["YYYY","MM","DD"])
    df[["YYYY","MM","DD"]] = df[["YYYY","MM","DD"]].astype(int)

    # --- Filtro opcional por fecha ---
    if selected_date:
        day, month, year = selected_date.day, selected_date.month, selected_date.year
        df_filtered = df[(df["DD"]==day) & (df["MM"]==month) & (df["YYYY"]==year)]
    else:
        df_filtered = df[df["Shift"]=="Daily"]

    # --- Reemplazo nombres ---
    machine_map = {
        "83947050 | Bancos de prueba de tensión (7050)(1)": "Recken 7050 (JATCO)",
        "83947150 | Bancos de prueba de tensión (7150) (1)": "Recken 7150 (HYUNDAI)",
        "83947250 | Bancos de prueba de tensión (7250) (1)": "Recken 7250 (GM/SUBARU)",
        "12525645 | Estación de inspección 100% (1)": "VPK 1",
        "12710703 | Estación de inspección 100% (2)": "VPK 2"
    }
    df_filtered["Machine"] = df_filtered["Machine"].replace(machine_map)

    # --- Targets ---
    target_recken = 85
    target_vpk = 65

    # --- Colorear OEE ---
    def color_oee(val, target):
        if pd.isna(val): return ""
        return "background-color: lightgreen" if target-5 <= val <= target+5 else "background-color: lightcoral"

    # --- Mostrar tablas por máquina ---
    for machine in df_filtered["Machine"].unique():
        st.subheader(f"{machine}" + (f" - Fecha: {selected_date}" if selected_date else ""))
        df_machine = df_filtered[df_filtered["Machine"] == machine]
        if "Recken" in machine:
            df_styled = df_machine.style.applymap(lambda v: color_oee(v, target_recken), subset=["Act.-OEE [%]"])
        elif "VPK" in machine:
            df_styled = df_machine.style.applymap(lambda v: color_oee(v, target_vpk), subset=["Act.-OEE [%]"])
        else:
            df_styled = df_machine
        st.dataframe(df_styled, hide_index=True, column_order=("DD","Shift","Act.-OEE [%]","AF [%]","PF [%]","QF [%]"))
        st.markdown("---")

    # --- Calcular OEE por máquina ---
    def calc_oee_formula(df_machine):
        df_shift = df_machine[df_machine["Shift"] != "Daily"].copy()
        if df_shift.empty: return np.nan
        cols = ["Production min.", "Planned min. (plan. op. time)", "Planned min. (Prod. qty.)", "Yield qty.", "Prod. qty."]
        df_shift[cols] = df_shift[cols].fillna(0)
        oee_series = (
            (df_shift["Production min."] / df_shift["Planned min. (plan. op. time)"].replace(0, np.nan)) *
            (df_shift["Planned min. (Prod. qty.)"] / df_shift["Production min."].replace(0, np.nan)) *
            (df_shift["Yield qty."] / df_shift["Prod. qty."].replace(0, np.nan))
        )
        return oee_series.mean() * 100

    recken_machines = ["Recken 7050 (JATCO)", "Recken 7150 (HYUNDAI)", "Recken 7250 (GM/SUBARU)"]
    vpk_machines = ["VPK 1", "VPK 2"]

    oee_dict = {}
    if selected_date:
        for m in recken_machines + vpk_machines:
            df_daily = df_filtered[(df_filtered["Machine"] == m) & (df_filtered["Shift"] == "Daily")]
            oee_dict[m] = df_daily["Act.-OEE [%]"].values[0] if not df_daily.empty else np.nan
    else:
        for m in recken_machines + vpk_machines:
            oee_dict[m] = calc_oee_formula(df_filtered[df_filtered["Machine"] == m])

    # --- KPIs globales ---
    def calc_global(oee_list):
        vals = [v for v in oee_list if not np.isnan(v)]
        return np.mean(vals) if vals else np.nan

    oee_global_recken = calc_global([oee_dict[m] for m in recken_machines])
    oee_global_vpk = calc_global([oee_dict[m] for m in vpk_machines])

    # --- Tarjetas ---
    st.markdown("### 🏭 OEE por Máquina")
    cols = st.columns(len(oee_dict))
    for idx, (machine, val) in enumerate(oee_dict.items()):
        if np.isnan(val): color = "red"; display_val = 0
        elif "Recken" in machine: color = "green" if target_recken-5 <= val <= target_recken+5 else "red"; display_val = val
        elif "VPK" in machine: color = "green" if target_vpk-5 <= val <= target_vpk+5 else "red"; display_val = val
        else: color = "red"; display_val = val
        with cols[idx]:
            st.markdown(f"""
            <div style='background-color:#f7f5f5; padding:15px; border-radius:10px; border:8px solid {color}; text-align:center'>
                <h5 style='color:black'>{machine}</h5>
                <h3 style='color:black'>{display_val:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)

    # --- Global cards ---
    cols = st.columns(2)
    with cols[0]:
        color = "green" if not np.isnan(oee_global_recken) and (target_recken-5 <= oee_global_recken <= target_recken+5) else "red"
        val = 0 if np.isnan(oee_global_recken) else oee_global_recken
        st.markdown(f"""
        <div style='background-color:#f7f5f5; padding:20px; border-radius:10px; border:8px solid {color}; text-align:center'>
            <h4 style='color:black'>Recken Global</h4>
            <h2 style='color:black'>{val:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        color = "green" if not np.isnan(oee_global_vpk) and (target_vpk-5 <= oee_global_vpk <= target_vpk+5) else "red"
        val = 0 if np.isnan(oee_global_vpk) else oee_global_vpk
        st.markdown(f"""
        <div style='background-color:#f7f5f5; padding:20px; border-radius:10px; border:8px solid {color}; text-align:center'>
            <h4 style='color:black'>VPK Global</h4>
            <h2 style='color:black'>{val:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    # --- Gráficas ---
    st.markdown("---")
    st.subheader("📊 Gráficas OEE - Recken")
    df_plot = df_filtered[df_filtered["Machine"].isin(recken_machines) & (df_filtered["Shift"]=="Daily")].copy()
    if not df_plot.empty:
        plt.figure(figsize=(12,4))
        colors = {
            "Recken 7050 (JATCO)":"#004A30",
            "Recken 7150 (HYUNDAI)":"#003984",
            "Recken 7250 (GM/SUBARU)":"#0671D8"
        }
        for machine in recken_machines:
            df_m = df_plot[df_plot["Machine"]==machine]
            plt.bar(df_m["DD"]+recken_machines.index(machine)*0.2,
                    df_m["Act.-OEE [%]"], width=0.2,
                    color=colors[machine], label=machine, edgecolor='black')
        plt.axhline(y=target_recken, color='red', linestyle='--', linewidth=2, label=f'Target {target_recken}%')
        plt.xticks(range(1,32)); plt.yticks(range(0,125,5)); plt.ylim(0,120)
        plt.title("Evolución diaria de OEE - Máquinas Recken")
        plt.grid(axis='y', linestyle='--', alpha=0.5); plt.legend()
        st.pyplot(plt.gcf()); plt.clf()
    else:
        st.warning("No hay datos disponibles para Recken")

    st.subheader("📊 Gráficas OEE - VPK")
    df_plot_vpk = df_filtered[(df_filtered["Machine"].isin(vpk_machines)) & (df_filtered["Shift"]=="Daily")].copy()
    if not df_plot_vpk.empty:
        plt.figure(figsize=(12,4))
        colors_vpk = {"VPK 1":"#9C27B0", "VPK 2":"#FF5722"}
        for machine in vpk_machines:
            df_m = df_plot_vpk[df_plot_vpk["Machine"]==machine]
            plt.bar(df_m["DD"]+vpk_machines.index(machine)*0.2,
                    df_m["Act.-OEE [%]"], width=0.2,
                    color=colors_vpk[machine], label=machine, edgecolor='black')
        plt.axhline(y=target_vpk, color='red', linestyle='--', linewidth=2, label=f'Target {target_vpk}%')
        plt.xticks(range(1,32)); plt.yticks(range(0,125,5)); plt.ylim(0,120)
        plt.title("Evolución diaria de OEE - Máquinas VPK")
        plt.grid(axis='y', linestyle='--', alpha=0.5); plt.legend()
        st.pyplot(plt.gcf()); plt.clf()
    else:
        st.warning("No hay datos disponibles para VPK")
