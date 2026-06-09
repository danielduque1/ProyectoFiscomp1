import ROOT
import Garfield
import numpy as np
import queue
import threading
import time

# Set up the gas medium.
gas = ROOT.Garfield.MediumMagboltz()
gas.SetTemperature(293.15)
gas.SetPressure(740.)
gas.SetComposition("ar", 70., "co2", 30.)
gas.EnableDrift()

# Read in the 2D field map.
elm = ROOT.Garfield.ComponentElmer2d("FEM/wire2d/mesh.header", "FEM/wire2d/mesh.elements", "FEM/wire2d/mesh.nodes", 
                                     "FEM/wire2d/dielectrics.dat", "FEM/wire2d/wire2d.result", "cm")
elm.SetMedium(0, gas)

# Create a Sensor object.
axis_x = axis_y = axis_z = 5
sensor = ROOT.Garfield.Sensor()
sensor.AddComponent(elm)
sensor.SetArea(-axis_x, -axis_y, -axis_z, axis_x, axis_y, axis_z)

# Create the avalanche object.
aval = ROOT.Garfield.AvalancheMicroscopic()
aval.SetSensor(sensor)
aval.SetCollisionSteps(10)

# Set up a viewer for the drift lines.
viewDrift = ROOT.Garfield.ViewDrift()
viewDrift.SetArea(-axis_x, -axis_y, -axis_z, axis_x, axis_y, axis_z)
aval.EnablePlotting(viewDrift)

# Set up and launch the avalanche.
ri = 4.0
thetai = np.random.uniform() * 2 * np.pi
xi = ri * np.cos(thetai)
yi = ri * np.sin(thetai)
zi = 0
aval.AvalancheElectron(xi, yi, zi, 0., 0., 0., 0., 0.)

# Plot the geometry and drift line.
cGeom = ROOT.TCanvas("geom", "Geometry")
viewMesh = ROOT.Garfield.ViewFEMesh()
viewMesh.SetArea(-axis_x, -axis_z, -axis_y, axis_x, axis_z, axis_y)
viewMesh.SetCanvas(cGeom)
viewMesh.SetComponent(elm)
viewMesh.SetPlane(0, 0, 1, 0, 0, 0)
viewMesh.SetFillMesh(False)
viewMesh.SetColor(1,ROOT.kGray)
viewMesh.EnableAxes()
viewMesh.SetXaxisTitle("x (cm)")
viewMesh.SetYaxisTitle("y (cm)")
viewMesh.SetViewDrift(viewDrift)
viewMesh.Plot()
cGeom.Draw()

# Plot the fields.
cFields = ROOT.TCanvas("fields", "Fields")
viewField = ROOT.Garfield.ViewField()
viewField.SetSensor(sensor)
viewField.SetCanvas(cFields)
viewField.SetArea(-axis_x, -axis_y, axis_x, axis_y)
viewField.SetNumberOfContours(20)
viewField.SetNumberOfSamples2d(30, 30)
viewField.SetPlane(0, 0, 1, 0, 0, 0)
viewField.PlotContour("v")
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
