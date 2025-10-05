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
    DAY, MONTH, YEAR = df.loc[0, ['DD','MM','YYYY']]

    df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")] + ['Date','DD','MM','YYYY'], inplace=True, errors='ignore')
    df['Station'] = df['Station'].where(df['Station'].str.startswith("Reckstation", na=False)).ffill()

    for col in ['Serie Parts','Rework Parts','Total Parts'] + orden_partes:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df.drop([12,13,14,15], axis = 0, inplace=True, errors='ignore')

    # --- Nuevo enfoque ---
    records = []
    for shift, group in df.groupby('Shift'):
        for parte in orden_partes:
            serie_total = group[parte].sum()
            rework_total = group[parte][group['Rework Parts'] > 0].sum()  # suma solo si hubo rework en esa estación
            records.append({
                'Shift': shift,
                'Parte': parte,
                'Serie Total': serie_total,
                'Rework Total': rework_total
            })

    ALDS_Recken = pd.DataFrame(records)
    ALDS_Recken['Shift'] = pd.Categorical(ALDS_Recken['Shift'], categories=shifts, ordered=True)
    ALDS_Recken['Parte'] = pd.Categorical(ALDS_Recken['Parte'], categories=orden_partes, ordered=True)
    ALDS_Recken = ALDS_Recken.sort_values(['Shift','Parte']).reset_index(drop=True)

    return ALDS_Recken
