import pandas as pd

def cargar_oee(file):
    orden_partes = ["L-0G005-1036-17", "L-0G005-0095-41", "L-0G005-1015-05", "L-0G005-1043-12"]
    shifts = ["1st Shift", "2nd Shift", "3rd Shift"]
    index_completo = pd.MultiIndex.from_product([shifts, orden_partes], names=["Shift", "Parte"])

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip().str.replace("\xa0", "").str.replace("\n", " ")
    df.dropna(how="all", inplace=True)

    turno_map = {"PRIMERO": "1st Shift", "SEGUNDO": "2nd Shift", "TERCERO": "3rd Shift"}
    turno_actual = None
    turnos = []

    for _, row in df.iterrows():
        row_str = row.astype(str).str.upper().str.strip()
        found = False
        for val in row_str:
            if val in turno_map:
                turno_actual = turno_map[val]
                found = True
                break
        turnos.append(None if found else turno_actual)

    df["Turno"] = turnos
    df = df[df["Turno"].notna()].reset_index(drop=True)
    col_turno = df["Turno"].copy()
    df.columns = df.iloc[0]
    df = df.drop(index=0).reset_index(drop=True)
    df["Turno"] = col_turno.iloc[1:].reset_index(drop=True)
    df['No. de Parte'] = df['No. de Parte'].ffill()

    df[["Maquina", "Parte"]] = df["No. de Parte"].astype(str).str.split("\n", expand=True)
    df["Piezas\nProd."] = pd.to_numeric(df["Piezas\nProd."], errors="coerce").fillna(0).astype(int)

    pivot = df.pivot_table(
        index=["Turno", "Parte"],
        columns=df["Descripción"],
        values="Piezas\nProd.",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    pivot = pivot.rename(columns={"Turno": "Shift", "Serie OK": "OEE Serie", "Retrabajo OK": "OEE Rework", "Chatarra de Serie": "OEE SCRAP"})
    pivot["Parte"] = pivot["Parte"].str.strip()
    pivot["Parte"] = pd.Categorical(pivot["Parte"], categories=orden_partes, ordered=True)

    pivot = pivot.set_index(["Shift", "Parte"]).reindex(index_completo, fill_value=0).reset_index()
    pivot[["OEE Serie", "OEE Rework", "OEE SCRAP"]] = pivot[["OEE Serie", "OEE Rework", "OEE SCRAP"]].astype(int)

    return pivot

