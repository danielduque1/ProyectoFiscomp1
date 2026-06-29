#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def visualizar_histograma(archivo_csv):
    # 1. Leer los datos
    try:
        df = pd.read_csv(archivo_csv)
    except FileNotFoundError:
        print(f"Error: No se encuentra el archivo {archivo_csv}")
        return

    df = df[df['Electrones'] != 0]
    df['Energia_etiqueta'] = df['Energia_eV'].astype(str)

    plt.figure(figsize=(10, 6))
    sns.histplot(
        data=df,
        x='Electrones',
        bins=120,
        multiple='layer',
        element='bars',
        stat='count',
        common_norm=False,
        alpha=0.7,
        palette='Set2',
    )
    plt.show()

    # 2. Configurar el gráfico
    plt.figure(figsize=(10, 6))
    
    # Histograma con separación por energía usando hue
    sns.histplot(
        data=df,
        x='Electrones',
        hue='Energia_etiqueta',
        bins=120,
        multiple='layer',
        element='bars',
        stat='count',
        common_norm=False,
        alpha=0.7,
        palette='Set2',
    )
    
    # 3. Etiquetas y estética
    plt.title('Distribución de Carga Recolectada por Energía', fontsize=14)
    plt.xlabel('Número de electrones recolectados', fontsize=12)
    plt.ylabel('Frecuencia (Conteos)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Mostrar el gráfico
    print("Mostrando histograma... Cierra la ventana para terminar.")
    plt.show()


if __name__ == "__main__":
    archivo1 = "datos_espectro_fe55_5000.csv"
    archivo2 = "datos_espectro_fe55_prob5000.csv"

    visualizar_histograma(archivo1)
    visualizar_histograma(archivo2)
