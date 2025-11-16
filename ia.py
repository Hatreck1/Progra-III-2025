import pandas as pd

ruta = "notas.csv"
notas = pd.read_csv(ruta, sep=";", encoding="utf-8")

print(notas)