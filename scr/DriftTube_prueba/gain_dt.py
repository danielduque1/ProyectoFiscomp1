import sys
import math
import logging
import numpy as np
import ROOT
import Garfield

# =========================================================================
# 0. CONFIGURACIÓN DEL SISTEMA DE LOGS (.LOG)
# =========================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("calibracion.log", mode="w"),
        logging.StreamHandler(sys.stdout)
    ]
)

if ROOT.gSystem.Load("libGarfield") < 0:
    logging.error("No se pudo cargar libGarfield de forma dinámica.")
    sys.exit(1)

# =========================================================================
# 1. CONFIGURACIÓN DEL GAS, EFECTO PENNING Y CAMPO ELÉCTRICO FEM
# =========================================================================
logging.info("Cargando archivos de Magboltz y movilidad de iones...")
gas = ROOT.Garfield.MediumMagboltz()
gas.LoadGasFile('ar_93_co2_7_3bar.gas')
gas.LoadIonMobility('/home/daniel/garfield/install/share/Garfield/Data/IonMobility_Ar+_Ar.txt')
gas.EnableDrift()

# CORRECCIÓN DE API Y COMPONENTE DONADORA CRÍTICA:
# Cambiado a EnablePenningTransfer y apuntando a "ar" como el gas excitado.
r_Penning = 0.51
p_scale = 0.0
gas.EnablePenningTransfer(r_Penning, p_scale, "ar")
gas.SetMaxElectronEnergy(150.0)

logging.info(f"Efecto Penning activado: Eficiencia r_P = {r_Penning * 100}% sobre los estados excitados del Argon.")

logging.info("Inicializando mapa de campo 2D desde Elmer FEM...")
elm = ROOT.Garfield.ComponentElmer2d(
    "FEM/drift_tube/mesh.header",
    "FEM/drift_tube/mesh.elements",
    "FEM/drift_tube/mesh.nodes",
    "FEM/drift_tube/dielectrics.dat",
    "FEM/drift_tube/drift_tube.result",
    "cm"
)
elm.SetMedium(0, gas)
elm.SetMedium(1, gas)

# =========================================================================
# 2. CONFIGURACIÓN DEL SENSOR Y MOTOR MICROSCÓPICO (TOWNSEND)
# =========================================================================
axis_lim = 1.2
sensor = ROOT.Garfield.Sensor()
sensor.AddComponent(elm)
sensor.SetArea(-axis_lim, -axis_lim, -axis_lim, axis_lim, axis_lim, axis_lim)

# Instanciamos el motor microscópico para el conteo de la avalancha real
aval = ROOT.Garfield.AvalancheMicroscopic()
aval.SetSensor(sensor)

# =========================================================================
# 3. BUCLE DE CALIBRACIÓN (MUESTREO ESTADÍSTICO)
# =========================================================================
n_electrones_prueba = 10 
lista_ganancias = []

# Posición inicial del electrón de prueba (a 1 mm del centro en el eje X)
x0 = 0.1  
y0 = 0.0
z0 = 0.0
t0 = 0.0
e0 = 0.0 

logging.info("=======================================================")
logging.info("INICIANDO CALIBRACIÓN MICROSCÓPICA DE GANANCIA INTRÍNSECA")
logging.info("=======================================================")
logging.info("Mezcla: Ar/CO2 (93/7) a 3 bar con corrección Penning.")
logging.info(f"Simulando {n_electrones_prueba} avalanchas microscópicas individuales...\n")

for i in range(n_electrones_prueba):
    # Lanza un único electrón y calcula microscópicamente toda su cascada de choques
    aval.AvalancheElectron(x0, y0, z0, t0, e0, 0.0, 0.0, 0.0)
    
    # Extraer los puntos finales calculados por AvalancheMicroscopic
    ganancia_evento = aval.GetNumberOfElectronEndpoints()
    lista_ganancias.append(ganancia_evento)
    
    if (i + 1) % 5 == 0:
        logging.info(f"   -> Progreso: {i + 1}/{n_electrones_prueba} avalanchas procesadas (Última G: {ganancia_evento})")

# =========================================================================
# 4. ANÁLISIS ESTADÍSTICO DE RESULTADOS Y ESCRITURA FINAL EN LOG
# =========================================================================
ganancia_media = np.mean(lista_ganancias)
desviacion_estandar = np.std(lista_ganancias)
ganancia_max = np.max(lista_ganancias)
ganancia_min = np.min(lista_ganancias)

logging.info("\n=======================================================")
logging.info("PROCESAMIENTO DE DATOS COMPLETADO")
logging.info("=======================================================")
logging.info(f"Ganancia Mínima Registrada: {ganancia_min:.1f}")
logging.info(f"Ganancia Máxima Registrada: {ganancia_max:.1f}")
logging.info(f"Desviación Estándar (Sigma): {desviacion_estandar:.1f}")
logging.info("\nVALOR CRÍTICO PARA TU SCRIPT PRINCIPAL:")
logging.info(f"--> GANANCIA MEDIA (G_bar): {ganancia_media:.2f}")
logging.info("=======================================================\n")
logging.info("Resultados volcados exitosamente en 'calibracion.log'.")