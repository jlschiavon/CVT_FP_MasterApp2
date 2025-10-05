import pandas as pd
from utils.helpers import asignar_turno

def cargar_mes(file):
    shifts = ["1st Shift", "2nd Shift", "3rd Shift"]
    orden_partes = ["L-0G005-1036-17", "L-0G005-0095-41", "L-0G005-1015-05", "L-0G005-1043-12"]
    partes_full = [parte + "    Chain CVT" for parte in orden_partes]
    index_completo = pd.MultiIndex.from_product([shifts, orden_partes], names=["Shift", "Parte"])

    dfMES = pd.read_excel(file)
    dfMES["Tiempo actual"] = pd.to_datetime(dfMES["Tiempo actual"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
    dfMES.dropna(subset=["Tiempo actual"], inplace=True)

    dfMES["Shift"] = dfMES["Tiempo actual"].apply(asignar_turno)
    dfMES = dfMES[dfMES["Operation"] == 20]
    dfMES["Texto del material"] = dfMES["Texto del material"].str.strip()

    tabla_mes = (
        dfMES.groupby(["Shift", "Texto del material"])["Piezas buenas"].sum()
        .reindex(pd.MultiIndex.from_product([shifts, partes_full], names=["Shift", "Texto del material"]), fill_value=0)
        .reset_index()
    )

    tabla_chatarra = (
        dfMES.groupby(["Shift", "Texto del material"])["Chatarra"].sum()
        .reindex(pd.MultiIndex.from_product([shifts, partes_full], names=["Shift", "Texto del material"]), fill_value=0)
        .reset_index()
    )

    tabla_mes["Parte"] = tabla_mes["Texto del material"].str.replace(r"\s+Chain CVT$", "", regex=True).str.strip()
    tabla_mes.drop(columns=["Texto del material"], inplace=True)
    tabla_mes = tabla_mes.rename(columns={"Piezas buenas": "MES"})

    tabla_chatarra["Parte"] = tabla_chatarra["Texto del material"].str.replace(r"\s+Chain CVT$", "", regex=True).str.strip()
    tabla_chatarra.drop(columns=["Texto del material"], inplace=True)
    tabla_chatarra = tabla_chatarra.rename(columns={"Chatarra": "MES SCRAP"})
    tabla_chatarra = tabla_chatarra.set_index(["Shift", "Parte"]).reindex(index_completo, fill_value=0).reset_index()

    return pd.merge(tabla_mes, tabla_chatarra, on=["Shift", "Parte"])
