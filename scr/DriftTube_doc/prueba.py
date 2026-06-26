#!/usr/bin/env python3
import sys
import math
import ctypes
import ROOT

print("=== Iniciando Script de Prueba de Rendimiento ===")

# 1. CARGAR LIBRERÍA
if ROOT.gSystem.Load("libGarfield") < 0:
    print("[Error] No se pudo cargar libGarfield")
    sys.exit(1)

MediumMagboltz   = ROOT.Garfield.MediumMagboltz
ComponentElmer2d = ROOT.Garfield.ComponentElmer2d
Sensor           = ROOT.Garfield.Sensor
AvalancheMC      = ROOT.Garfield.AvalancheMC

# 2. CONFIGURAR GAS
gas = MediumMagboltz()
if not gas.LoadGasFile("ar_70_co2_30.gas"):
    print("[Error] No se pudo cargar el gas")
    sys.exit(1)

# 3. CARGAR ELMER 2D
elm = ComponentElmer2d()
elm.Initialise(
    "FEM/drift_tube/mesh.header", 
    "FEM/drift_tube/mesh.elements", 
    "FEM/drift_tube/mesh.nodes", 
    "FEM/dielectrics.dat",  
    "FEM/drift_tube/drift_tube.result", 
    "cm"
)
elm.SetMedium(0, gas)
elm.SetMedium(1, gas)

# 4. CONFIGURAR SENSOR
axis_lim = 1.2
sensor = Sensor()
sensor.AddComponent(elm)
sensor.SetArea(-axis_lim, -axis_lim, -axis_lim, axis_lim, axis_lim, axis_lim)

# 5. CONFIGURAR AVALANCHA (Modo Drift Puro para Diagnóstico Rápido)
avalanche = AvalancheMC()
avalanche.SetSensor(sensor)
avalanche.SetDistanceSteps(0.01) # Pasos más grandes de 100 micras para ir rápido

# ¡ESTA LÍNEA EVITA QUE SE CONGELE EL TEST!
# Le dice a AvalancheMC que calcule solo la deriva (drift) del electrón y apague 
# la multiplicación exponencial en el alambre. Así mediremos la velocidad de la malla.

# Elimina la línea avalanche.EnableAvalanche(False) y pon esto:
# Desactiva la multiplicación gaseosa (Townsend) para que el electrón solo derive
avalanche.EnableMultiplication(False)

print("\n--- Todo inicializado con éxito. Lanzando 1 electrón de prueba ---")

# Disparamos un único electrón en x = 0.5 cm, y = 0.0 cm, z = 0.0 cm, t = 0.0 ns
x0, y0, z0, t0 = 0.5, 0.0, 0.0, 0.0
avalanche.AvalancheElectron(x0, y0, z0, t0)

nEndpoints = avalanche.GetNumberOfElectronEndpoints()
print(f"¡Simulación completada! El electrón generó: {nEndpoints} trayectorias de drift.")

# Leer el punto de destino final del electrón
if nEndpoints > 0:
    xStart, yStart, zStart, tStart = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
    xEnd, yEnd, zEnd, tEnd = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
    status = ctypes.c_int(0)
    
    avalanche.GetElectronEndpoint(0, xStart, yStart, zStart, tStart, xEnd, yEnd, zEnd, tEnd, status)
    
    r_final = math.sqrt(xEnd.value**2 + yEnd.value**2)
    print(f"-> El electrón inició en el gas a r = {xStart.value:.3f} cm")
    print(f"-> El electrón terminó su deriva en r = {r_final:.4f} cm (Código de estado final: {status.value})")

print("\n=== TEST FINALIZADO CON ÉXITO EN SEGUNDOS ===")