import pandas as pd
import streamlit as st
from utils.load_clean_alds import cargar_alds
from utils.load_clean_mes import cargar_mes

def procesar_recken(alds_df, mes_df):
    """
    Procesa los archivos ALDS y MES de Recken y devuelve un DataFrame unido.
    """

    # --- Procesar ALDS ---
    recken_alds_clean = cargar_alds({"05 - Overview (Parts worked in stations per shift)": alds_df})
    if recken_alds_clean is None or recken_alds_clean.empty:
        st.error("❌ Error: cargar_alds no devolvió datos válidos para Recken.")
        return None, None
    else:
        st.success("✅ ALDS_Recken generado correctamente")
        st.dataframe(recken_alds_clean, use_container_width=True)

    # --- Procesar MES ---
    df_mes = cargar_mes({"correctionQty)": mes_df})
    if df_mes is None or df_mes.empty:
        st.error("❌ Error: cargar_mes no devolvió datos válidos para Recken.")
        return recken_alds_clean, None
    else:
        st.success("✅ MES_Recken generado correctamente")
        st.dataframe(df_mes, use_container_width=True)

    # --- Unir DataFrames si ambos existen ---
    if recken_alds_clean is not None and not recken_alds_clean.empty \
       and df_mes is not None and not df_mes.empty:

        # Puedes cambiar la lógica de merge según la relación real
        df_final = pd.merge(
            recken_alds_clean,
            df_mes,
            on=["Part Number", "Shift"],  # claves de unión
            how="inner"
        )
        st.success("✅ DataFrames unidos correctamente")
        st.dataframe(df_final, use_container_width=True)

        return recken_alds_clean, df_final

    return recken_alds_clean, None
