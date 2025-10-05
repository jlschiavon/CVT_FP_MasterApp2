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

# Agrupar por Shift y sumar partes
ALDS_Recken = df.groupby('Shift')[orden_partes].sum().reset_index().melt(
    id_vars='Shift', value_vars=orden_partes,
    var_name='Parte', value_name='Total'
)

# Orden correcto de Shift y Parte
ALDS_Recken['Shift'] = pd.Categorical(ALDS_Recken['Shift'], categories=shifts, ordered=True)
ALDS_Recken['Parte'] = pd.Categorical(ALDS_Recken['Parte'], categories=orden_partes, ordered=True)
ALDS_Recken = ALDS_Recken.sort_values(['Shift','Parte']).reset_index(drop=True)
ALDS_Recken.drop([12,13,14,15], axis=0, inplace=True)  # Eliminar filas no deseadas


return pd.Dataframe(ALDS_Recken)



























import pandas as pd

# Constantes
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
    df.drop([0,1,2,3,4,5,6,7,8], axis=0, inplace=True)
    df.rename(columns={
        'Unnamed: 5': 'Date',
        'Unnamed: 6': 'DD',
        'Unnamed: 7': 'MM',
        'Unnamed: 8': 'YYYY'
    }, inplace=True)
    df.reset_index(drop=True, inplace=True)

    date_split = df["Date"].astype(str).str.split(".", expand=True)
    df["DD"], df["MM"], df["YYYY"] = date_split[0], date_split[1], date_split[2]

    df.drop([0,1,2,3,4], axis=0, inplace=True)

    df.rename(columns={
        'Unnamed: 1': 'Station',
        'Unnamed: 10': 'Shift',
        'Unnamed: 13': 'Serie Parts',
        'Unnamed: 17': 'Rework Parts',
        'Unnamed: 19': 'Total Parts',
        'Unnamed: 20': 'L-0G005-1036-17',
        'Unnamed: 23': 'L-0G005-0095-41',
        'Unnamed: 26': 'L-0G005-1015-05',
        'Unnamed: 29': 'L-0G005-1043-12'
    }, inplace=True)

    cols_to_drop = [col for col in df.columns if col.startswith("Unnamed")]
    df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
    df.drop(['Date', 'DD', 'MM', 'YYYY'], axis=1, inplace=True)

    df["Station"] = df["Station"].where(df["Station"].str.startswith("Reckstation", na=False)).ffill()

    df["Serie Parts"] = pd.to_numeric(df["Serie Parts"], errors="coerce").fillna(0)
    df["Rework Parts"] = pd.to_numeric(df["Rework Parts"], errors="coerce").fillna(0)
    df["Total Parts"] = pd.to_numeric(df["Total Parts"], errors="coerce").fillna(0)

    # ====== AGRUPACIÓN ======
    ALDS = []
    for shift in shifts:
        df_shift = df[df["Shift"] == shift]
        for parte in orden_partes:
            if parte not in df.columns:
                continue
            filtro = df_shift[parte] != 0
            total_serie = df_shift.loc[filtro, "Serie Parts"].sum()
            total_rework = df_shift.loc[filtro, "Rework Parts"].sum()
            ALDS.append({
                "Shift": shift,
                "Parte": parte,
                "ALDS Serie": total_serie,
                "ALDS Rework": total_rework
            })

    return pd.DataFrame(ALDS)  # ✅ Ahora sí se devuelve correctamente
