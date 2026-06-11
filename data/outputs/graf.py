import pandas as pd
import matplotlib.pyplot as plt

datos = pd.read_csv("data/outputs/carga_recolectada_anodo_170GeV.csv")
conteos = datos["Electrones_Finales_Anodo"]
conteos.plot(kind="hist", bins=50, color="blue", edgecolor="black")
plt.title("Histograma de Conteos de Electrones Finales (100 Muones)")
plt.xlabel("Número de Electrones Finales")  
plt.ylabel("Frecuencia")
plt.grid(axis="y", alpha=0.75)
plt.show()