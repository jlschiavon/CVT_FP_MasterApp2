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
