import pandas as pd

df = pd.read_csv("kode_wilayah_lanud_indonesia.csv")
print(df.columns.tolist())
print(df.head())
