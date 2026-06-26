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

    # 2. Configurar el gráfico
    plt.figure(figsize=(10, 6))
    
    # Histograma con separación por energía usando hue
    sns.histplot(
        data=df,
        x='Electrones',
        hue='Energia_etiqueta',
        bins=50,
        multiple='layer',
        element='bars',
        stat='count',
        common_norm=False,
        alpha=0.7,
        palette='Set2',
    )
    
    # 3. Etiquetas y estética
    plt.title('Distribución de Carga Recolectada por Energía (Espectro Fe-55)', fontsize=14)
    plt.xlabel('Número de electrones recolectados', fontsize=12)
    plt.ylabel('Frecuencia (Conteos)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Mostrar el gráfico
    print("Mostrando histograma... Cierra la ventana para terminar.")
    plt.show()

    # Histograma solo para Energia_eV = 7058.0
    df_7058 = df[df['Energia_eV'] == 7058.0]

    if not df_7058.empty:
        plt.figure(figsize=(10, 6))
        sns.histplot(
            data=df_7058,
            x='Electrones',
            bins=50,
            color='crimson',
            edgecolor='black',
            alpha=0.8,
        )
        plt.title('Histograma de Carga Recolectada para Energia_eV = 7058.0', fontsize=14)
        plt.xlabel('Número de electrones recolectados', fontsize=12)
        plt.ylabel('Frecuencia (Conteos)', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        print("Mostrando histograma de 7058.0... Cierra la ventana para terminar.")
        plt.show()
    else:
        print("No hay datos para Energia_eV = 7058.0 después de filtrar Electrones != 0.")

if __name__ == "__main__":
    archivo = "datos_espectro_fe55_colimado.csv"
    visualizar_histograma(archivo)