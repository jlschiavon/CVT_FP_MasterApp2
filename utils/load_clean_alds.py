import os
import pandas as pd

# ✅ Estas deben estar fuera de la función
shifts = ["1st Shift", "2nd Shift", "3rd Shift"]
orden_partes = ["L-0G005-1036-17", "L-0G005-0095-41", "L-0G005-1015-05", "L-0G005-1043-12"]

def cargar_alds(file):
    index_completo = pd.MultiIndex.from_product([shifts, orden_partes], names=["Shift", "Parte"])

df = pd.read_csv(r"C:\Users\jorge\OneDrive - Instituto Tecnologico y de Estudios Superiores de Monterrey\Desktop\Master App PF CVT\05 - Overview (Parts worked in stations per shift) (1).csv")
df.drop([0,1,2,3,4,5,6,7,8], axis=0, inplace=True)
df.rename(columns={'Unnamed: 5': 'Date'}, inplace=True)
df.rename(columns={'Unnamed: 6': 'DD'}, inplace=True)
df.rename(columns={'Unnamed: 7': 'MM'}, inplace=True)
df.rename(columns={'Unnamed: 8': 'YYYY'}, inplace=True)
df.reset_index(drop=True, inplace=True)

date_split = df["Date"].astype(str).str.split(".", expand=True)
df["DD"] = date_split[0]
df["MM"] = date_split[1]    
df["YYYY"] = date_split[2]

DAY = df.loc[0,"DD"]
MONTH = df.loc[0,"MM"]
YEAR = df.loc[0,"YYYY"]

df.drop([0,1,2,3,4], axis=0, inplace=True)

print("DAY: ",DAY)
print("MONTH: ",MONTH)
print("YEAR: ",YEAR)

df.rename(columns={'Unnamed: 1': 'Station'}, inplace=True)
df.rename(columns={'Unnamed: 10': 'Shift'}, inplace=True)
df.rename(columns={'Unnamed: 13': 'Serie Parts'}, inplace=True)
df.rename(columns={'Unnamed: 17': 'Rework Parts'}, inplace=True)
df.rename(columns={'Unnamed: 19': 'Total Parts'}, inplace=True)
df.rename(columns={'Unnamed: 20': 'L-0G005-1036-17'}, inplace=True)
df.rename(columns={'Unnamed: 23': 'L-0G005-0095-41'}, inplace=True)
df.rename(columns={'Unnamed: 26': 'L-0G005-1015-05'}, inplace=True)
df.rename(columns={'Unnamed: 29': 'L-0G005-1043-12'}, inplace=True)

cols_to_drop = [col for col in df.columns if col.startswith("Unnamed")]
df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
df.drop(['Date', 'DD', 'MM', 'YYYY'], axis=1, inplace=True)

df["Station"] = df["Station"].where(df["Station"].str.startswith("Reckstation", na=False)).ffill()

df["Serie Parts"] = pd.to_numeric(df["Serie Parts"], errors="coerce").fillna(0)
df["Rework Parts"] = pd.to_numeric(df["Rework Parts"], errors="coerce").fillna(0)
df["Total Parts"] = pd.to_numeric(df["Total Parts"], errors="coerce").fillna(0)

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

df_ALDS = pd.DataFrame(ALDS)
print(df_ALDS)
