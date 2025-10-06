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
    #df_original = df.copy()
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
    
    # Extraer día, mes, año
    df[['DD','MM','YYYY']] = df['Date'].astype(str).str.split(".", expand=True)
    DAY, MONTH, YEAR = df.loc[0, ['DD','MM','YYYY']]
    print("DAY:", DAY, "MONTH:", MONTH, "YEAR:", YEAR)
    
    df.drop(index=[0,1,2,3,4], inplace=True)  # Elimina la fila de encabezado original
    
    # Limpiar columnas innecesarias
    df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")] + ['Date','DD','MM','YYYY'], inplace=True, errors='ignore')
        
    # Completar nombres de estaciones
    df['Station'] = df['Station'].where(df['Station'].str.startswith("Reckstation", na=False)).ffill()
        
    # Convertir columnas numéricas
    for col in ['Serie Parts','Rework Parts','Total Parts'] + orden_partes:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df.drop(index = [5,6,7,8,9,10,11,12,13,38,39,40,41,42,43], inplace = True)
        
    # ====== CÁLCULO DE TOTALES ======
    
    resultados = []
    
    for shift in shifts:
        for part in orden_partes:
            val = df.loc[(df['Shift'] == shift) & (df["Serie Parts"] > 0), part].sum()
    
            if val > 0:
                total_series = df.loc[(df['Shift'] == shift) & (df[part] > 0), 'Serie Parts'].sum()
                total_rework = val - total_series
            else:
                total_series = 0
                total_rework = 0
    
            resultados.append({
                "Shift": shift,
                "Part Number": part,
                "ALDS Serie Parts Total": total_series,
                "ALDS Rework Parts Total": total_rework
            })
    
    ALDS_Recken = pd.DataFrame(resultados)
    return df_tratado
