import pandas as pd

def cargar_alds(file):
    shifts = ["1st Shift", "2nd Shift", "3rd Shift"]
    orden_partes = ["L-0G005-1036-17", "L-0G005-0095-41", "L-0G005-1015-05", "L-0G005-1043-12"]
    index_completo = pd.MultiIndex.from_product([shifts, orden_partes], names=["Shift", "Parte"])

    df = pd.read_csv(file, skiprows=14)
    df.dropna(how="all", axis=1, inplace=True)
    df.dropna(how="all", axis=0, inplace=True)
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]
    df["Station"] = df["Station"].where(df["Station"].str.startswith("Reckstation", na=False)).ffill()

    ALDS = []
    for shift in shifts:
        df_shift = df[df["Shift"] == shift]
        for parte in orden_partes:
            if parte not in df.columns:
                continue
            filtro = df_shift[parte] != 0
            total_serie = df_shift.loc[filtro, "Serie Parts"].sum() if filtro.any() else 0
            total_rework = df_shift.loc[filtro, "Rework Parts"].sum() if filtro.any() else 0
            ALDS.append({"Shift": shift, "Parte": parte, "ALDS Serie": total_serie, "ALDS Rework": total_rework})

    return pd.DataFrame(ALDS).set_index(["Shift", "Parte"]).reindex(index_completo, fill_value=0).reset_index()
