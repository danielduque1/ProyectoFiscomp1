import ROOT
import Garfield
import numpy as np
import queue
import threading
import time

# =========================================================================
# 1. CONFIGURACIÓN DEL MEDIO (GAS AR/CO2)
# =========================================================================
gas = ROOT.Garfield.MediumMagboltz()
gas.SetTemperature(293.15)      # 20 °C
gas.SetPressure(740.)           # Presión típica en Torr
gas.SetComposition("ar", 70., "co2", 30.)
gas.EnableDrift()

# =========================================================================
# 2. IMPORTAR EL MAPA DE CAMPO 2D DE ELMER (8 NODOS SERENDIPITY)
# =========================================================================
# Asegúrate de que la ruta apunte correctamente a la carpeta de tu malla
elm = ROOT.Garfield.ComponentElmer2d(
    "FEM/drift_tube/mesh.header",
    "FEM/drift_tube/mesh.elements",
    "FEM/drift_tube/mesh.nodes",
    "FEM/drift_tube/dielectrics.dat",  # Tu archivo .dat manual de 2 materiales
    "FEM/drift_tube/drift_tube.result",
    "cm"
)

# Asociar el gas a ambos cuerpos geométricos indexados
elm.SetMedium(0, gas)  # Material 1 (Gas) -> Índice 0 en Garfield++
elm.SetMedium(1, gas)  # Material 2 (Alambre) -> Índice 1 en Garfield++

# =========================================================================
# 3. CONFIGURACIÓN DEL SENSOR Y ÁREA DE SIMULACIÓN
# =========================================================================
# Definimos el área en cm (un cubo de 1.2 cm de lado para encerrar el tubo de 1 cm)
axis_x = axis_y = 1.2
axis_z = 1.2

sensor = ROOT.Garfield.Sensor()
sensor.AddComponent(elm)
sensor.SetArea(-axis_x, -axis_y, -axis_z, axis_x, axis_y, axis_z)

# =========================================================================
# 4. CONFIGURACIÓN DE LA AVALANCHA MICROSCÓPICA
# =========================================================================
aval = ROOT.Garfield.AvalancheMicroscopic()
aval.SetSensor(sensor)
aval.SetCollisionSteps(10)

# Configurar el visor de las líneas de deriva (Drift Lines)
viewDrift = ROOT.Garfield.ViewDrift()
viewDrift.SetArea(-axis_x, -axis_y, -axis_z, axis_x, axis_y, axis_z)
aval.EnablePlotting(viewDrift)

# =========================================================================
# 5. LANZAMIENTO DEL ELECTRÓN PRIMARIO
# =========================================================================
# Colocamos el electrón inicial a una distancia radial ri = 0.5 cm (mitad del tubo)
ri = 0.5
thetai = np.random.uniform() * 2 * np.pi
xi = ri * np.cos(thetai)
yi = ri * np.sin(thetai)
zi = 0.0

print(f"Lanzando electrón primario en la posición radial: ({xi:.4f}, {yi:.4f}, {zi:.4f}) cm")
aval.AvalancheElectron(xi, yi, zi, 0., 0., 0., 0., 0.)

# =========================================================================
# 6. GRAFICAR LA GEOMETRÍA Y LAS LÍNEAS DE DERIVA
# =========================================================================
cGeom = ROOT.TCanvas("geom", "Geometry - Drift Tube")
viewMesh = ROOT.Garfield.ViewFEMesh()
viewMesh.SetArea(-axis_x, -axis_z, -axis_y, axis_x, axis_z, axis_y)
viewMesh.SetCanvas(cGeom)
viewMesh.SetComponent(elm)
viewMesh.SetPlane(0, 0, 1, 0, 0, 0)  # Plano de corte Z = 0
viewMesh.SetFillMesh(False)
viewMesh.SetColor(1, ROOT.kGray)
viewMesh.EnableAxes()
viewMesh.SetXaxisTitle("x (cm)")
viewMesh.SetYaxisTitle("y (cm)")
viewMesh.SetViewDrift(viewDrift)
viewMesh.Plot()
cGeom.Draw()

# =========================================================================
# 7. GRAFICAR EL CONTORNO DEL POTENCIAL ELECTROSTÁTICO
# =========================================================================
cFields = ROOT.TCanvas("fields", "Equipotential Lines")
viewField = ROOT.Garfield.ViewField()
viewField.SetSensor(sensor)
viewField.SetCanvas(cFields)
viewField.SetArea(-axis_x, -axis_y, axis_x, axis_y)
viewField.SetNumberOfContours(20)       # 20 líneas equipotenciales
viewField.SetNumberOfSamples2d(30, 30)
viewField.SetPlane(0, 0, 1, 0, 0, 0)
viewField.PlotContour("v")              # "v" para graficar Voltaje
cFields.Draw()

# Keep processing ROOT events until "q" is entered in the terminal.
commands = queue.Queue()


def read_commands():
    while True:
        try:
            command = input("Ingrese q para terminar: ").strip().lower()
        except EOFError:
            command = "q"
        commands.put(command)
        if command == "q":
            return


threading.Thread(target=read_commands, daemon=True).start()

while True:
    ROOT.gSystem.ProcessEvents()
    try:
        if commands.get_nowait() == "q":
            break
    except queue.Empty:
        pass
    time.sleep(0.05)

cGeom.Close()
cFields.Close()