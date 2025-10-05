from datetime import datetime
import pandas as pd

def asignar_turno(ts):
    h = ts.hour + ts.minute / 60
    if 7 <= h < 15:
        return "1st Shift"
    elif 15 <= h < 22.5:
        return "2nd Shift"
    else:
        return "3rd Shift"

def generar_union_final(df_alds=None, df_mes=None, df_oee=None):
    # Filtrar columnas del OEE si el DataFrame no es None
    if df_oee is not None and not df_oee.empty:
        columnas_oee_deseadas = ["Shift", "Parte", "OEE Serie", "OEE Rework", "OEE SCRAP"]
        columnas_disponibles = [col for col in columnas_oee_deseadas if col in df_oee.columns]
        df_oee = df_oee[columnas_disponibles]

    # Lista para acumular los DataFrames válidos
    dataframes = []

    if df_alds is not None and not df_alds.empty:
        dataframes.append(df_alds)

    if df_mes is not None and not df_mes.empty:
        dataframes.append(df_mes)

    if df_oee is not None and not df_oee.empty:
        dataframes.append(df_oee)

    if not dataframes:
        return pd.DataFrame(columns=[
            "Shift", "Parte", "MES",
            "ALDS Serie", "ALDS Rework",
            "OEE Serie", "OEE Rework", "OEE SCRAP"
        ])

    # Realizar merge progresivo sobre "Shift" y "Parte"
    tabla_final = dataframes[0]
    for df in dataframes[1:]:
        tabla_final = pd.merge(tabla_final, df, on=["Shift", "Parte"], how="outer")

    # Rellenar valores faltantes y asegurar formato
    tabla_final["Shift"] = tabla_final["Shift"].fillna("Sin turno").astype(str)
    tabla_final["Parte"] = tabla_final["Parte"].fillna("Sin parte").astype(str)
    tabla_final.fillna(0, inplace=True)

    # Orden específico de columnas
    columnas_ordenadas = ["Shift", "Parte","MES","ALDS Serie", "ALDS Rework","OEE Serie", "OEE Rework", "MES SCRAP", "Físico", "OEE SCRAP"]
    
    # Agregar columnas que existan, en orden, y omitir las que no
    columnas_presentes = [col for col in columnas_ordenadas if col in tabla_final.columns]

    tabla_final = tabla_final[columnas_presentes]

    return tabla_final
