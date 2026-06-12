import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ruta_csv = Path(__file__).resolve().with_name("linea_1_kind_250000000.0.csv")
datos = pd.read_csv(ruta_csv)
conteos = datos["Electrones_Finales_Anodo"]
conteos.plot(kind="hist", bins=50, color="blue", edgecolor="black")
plt.title("Histograma de Conteos de Electrones Finales (100 Muones)")
plt.xlabel("Número de Electrones Finales")  
plt.ylabel("Frecuencia")
plt.grid(axis="y", alpha=0.75)
plt.show()
