
import pandas as pd

# Configuración de shifts y partes
shifts = ["1st Shift", "2nd Shift", "3rd Shift"]
orden_partes = ["L-0G005-1036-17", "L-0G005-0095-41", "L-0G005-1015-05", "L-0G005-1043-12"]

def cargar_alds(files_dict):
    # Buscar el archivo que contenga '05 - overview' dentro de las keys del diccionario
    for key, df in files_dict.items():
        if "05 - overview" in key.lower():
            return procesar_alds_recken(df)  # ✅ Procesar solo ese dataframe
    
    return None  # Si no se encuentra

def procesar_alds_recken(df):
    # ====== LIMPIEZA INICIAL ======
    df = df.copy()
    column_map = {
    'Unnamed: 1': 'Station',
    'Unnamed: 10': 'Shift',
    'Unnamed: 13': 'Serie Parts',
    'Unnamed: 17': 'Rework Parts',
    'Unnamed: 19': 'Total Parts',
    'Unnamed: 20': orden_partes[0],
    'Unnamed: 23': orden_partes[1],
    'Unnamed: 26': orden_partes[2],
    'Unnamed: 29': orden_partes[3],
    'Unnamed: 5': 'Date'
    }
    
    df.rename(columns=column_map, inplace=True)
    
    # Extraer día, mes, año de la fecha
    df[['DD','MM','YYYY']] = df['Date'].astype(str).str.split(".", expand=True)
    DAY, MONTH, YEAR = df.loc[0, ['DD','MM','YYYY']]
    print("DAY:", DAY, "MONTH:", MONTH, "YEAR:", YEAR)
    
    # Limpiar columnas innecesarias
    df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")] + ['Date','DD','MM','YYYY'], inplace=True, errors='ignore')
    
    # Completar nombres de estaciones
    df['Station'] = df['Station'].where(df['Station'].str.startswith("Reckstation", na=False)).ffill()
    
    # Convertir columnas numéricas
    for col in ['Serie Parts','Rework Parts','Total Parts'] + orden_partes:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Eliminar filas finales vacías si existen
    df = df.iloc[:-6, :]

    # --- Agrupar por Shift y Parte ---
    serie_df = df.groupby('Shift')[orden_partes].sum().reset_index().melt(
        id_vars='Shift', value_vars=orden_partes,
        var_name='Parte', value_name='Serie Total'
    )

    rework_df = df.groupby('Shift')[orden_partes].sum().reset_index().melt(
        id_vars='Shift', value_vars=orden_partes,
        var_name='Parte', value_name='Rework Total'
    )

    # Combinar ambos
    ALDS_Recken = pd.merge(serie_df, rework_df, on=['Shift','Parte'])

    # Ordenar
    ALDS_Recken['Shift'] = pd.Categorical(ALDS_Recken['Shift'], categories=shifts, ordered=True)
    ALDS_Recken['Parte'] = pd.Categorical(ALDS_Recken['Parte'], categories=orden_partes, ordered=True)
    ALDS_Recken = ALDS_Recken.sort_values(['Shift','Parte']).reset_index(drop=True)
    
    return ALDS_Recken
