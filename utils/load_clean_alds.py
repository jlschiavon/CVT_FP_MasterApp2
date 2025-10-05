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

    df[['DD','MM','YYYY']] = df['Date'].astype(str).str.split(".", expand=True)
    df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")] + ['Date','DD','MM','YYYY'], inplace=True, errors='ignore')
    
    df['Station'] = df['Station'].where(df['Station'].str.startswith("Reckstation", na=False)).ffill()
    
    for col in ['Serie Parts','Rework Parts','Total Parts'] + orden_partes:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df.drop([12,13,14,15], axis=0, inplace=True, errors='ignore')

    index_completo = pd.MultiIndex.from_product([shifts, orden_partes], names=["Shift", "Parte"])

    ALDS = []
    for shift in shifts:
        df_shift = df[df["Shift"] == shift]
        for parte in orden_partes:
            if parte not in df.columns:
                continue
            total_serie = df_shift[parte].sum()           # suma todos los valores de esa parte
            total_rework = df_shift["Rework Parts"].sum() # suma todas las filas de Rework Parts
            ALDS.append({
                "Shift": shift,
                "Parte": parte,
                "Serie Total": total_serie,
                "Rework Total": total_rework
            })

    ALDS_Recken = pd.DataFrame(ALDS).set_index(["Shift", "Parte"]).reindex(index_completo, fill_value=0).reset_index()
    return ALDS_Recken
