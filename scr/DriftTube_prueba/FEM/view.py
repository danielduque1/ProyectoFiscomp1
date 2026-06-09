import pyvista as pv
import matplotlib.pyplot as plt
import numpy as np

# 1. Cargar el archivo de resultados desde la subcarpeta
ruta_vtu = "drift_tube/case_t0001.vtu"  # 🌟 Ruta exacta detectada
try:
    mesh = pv.read(ruta_vtu)
    print(f"Archivo {ruta_vtu} cargado con éxito.")
except Exception as e:
    print(f"Error: No se pudo leer el archivo en {ruta_vtu}")
    raise e

# 2. Extraer las coordenadas de los nodos (X, Y) y el Potencial
puntos = mesh.points  # Matriz de Nx3 (X, Y, Z)
X = puntos[:, 0]
Y = puntos[:, 1]

# Extraer el potencial (Elmer lo guarda en minúsculas por defecto en VTU)
potencial = mesh.point_data["potential"]

# 3. Interpolar los datos a una grilla regular y aplicar máscara circular
num_puntos_grilla = 400  # Aumentar la resolución de la grilla ayuda a suavizar
xi = np.linspace(X.min(), X.max(), num_puntos_grilla)
yi = np.linspace(Y.min(), Y.max(), num_puntos_grilla)
XI, YI = np.meshgrid(xi, yi)

# Interpolar con PyVista
grid_regular = pv.PolyData(np.column_stack((XI.ravel(), YI.ravel(), np.zeros_like(XI.ravel()))))
interpolado = grid_regular.sample(mesh)
ZI = interpolado.point_data["potential"].reshape(XI.shape)

# 🌟 LA MÁSCARA: Calcular la distancia radial de cada punto de la grilla al centro
R_grilla = np.sqrt(XI**2 + YI**2)
# Reemplazar con NaN (Not a Number) todo lo que esté más allá del radio del cátodo (1.0 cm)
ZI[R_grilla > 0.99] = np.nan  # Usamos 0.99 para limpiar justo antes del borde analítico

# 4. Configurar el gráfico con Matplotlib
plt.figure(figsize=(8, 7))

# Definir los niveles de las líneas equipotenciales (de 0V a 1500V cada 150V)
voltaje_maximo = 1500.0
niveles = np.arange(0, voltaje_maximo + 150, 150)

# Dibujar el mapa de calor de fondo
mapa_calor = plt.pcolormesh(XI, YI, ZI, cmap='viridis', shading='auto', vmin=0, vmax=voltaje_maximo)
cbar = plt.colorbar(mapa_calor)
cbar.set_label('Potencial Eléctrico (V)', fontsize=12)

# Dibujar las líneas equipotenciales (Contour)
lineas_contorno = plt.contour(XI, YI, ZI, levels=niveles, colors='white', linewidths=1.2)
plt.clabel(lineas_contorno, inline=True, fmt='%1.0f V', fontsize=9, colors='white')

# Detalles estéticos del gráfico
plt.title('Líneas Equipotenciales en el Drift Tube (Cálculo FEM)', fontsize=14, pad=15)
plt.xlabel('Posición X (cm)', fontsize=12)
plt.ylabel('Posición Y (cm)', fontsize=12)
plt.gca().set_aspect('equal') # Mantiene la simetría circular real
plt.grid(True, linestyle='--', alpha=0.3)

# Guardar la imagen en el disco
plt.savefig("equipotenciales_drift_tube.png", dpi=300, bbox_inches='tight')
print("Gráfico guardado con éxito como 'equipotenciales_drift_tube.png'")
plt.show()