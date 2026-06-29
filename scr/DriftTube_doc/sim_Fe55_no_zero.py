#!/usr/bin/env python3
import sys
import math
import random
import ctypes
import csv
import gc  # Garbage collector de Python para controlar los 10 GB de RAM
import ROOT
from tqdm import tqdm

# Activar modo batch para procesamiento eficiente en memoria
ROOT.gROOT.SetBatch(True)

# Cargar librería de Garfield
if ROOT.gSystem.Load("libGarfield") < 0:
    print("[Error] No se pudo cargar libGarfield")
    sys.exit(1)

# Aliases de clases
MediumMagboltz   = ROOT.Garfield.MediumMagboltz
ComponentElmer2d = ROOT.Garfield.ComponentElmer2d
Sensor           = ROOT.Garfield.Sensor
TrackHeed        = ROOT.Garfield.TrackHeed
AvalancheMC      = ROOT.Garfield.AvalancheMC

def main():
    # 1. Configuración del Gas
    gas = MediumMagboltz()
    if not gas.LoadGasFile("ar_70_co2_30.gas"):
        print("[Error] No se pudo cargar ar_70_co2_30.gas")
        sys.exit(1)
    gas.EnablePenningTransfer(0.30, 0.0, "ar")

    # 2. Configuración Elmer
    elm = ComponentElmer2d(
        "FEM/drift_tube/mesh.header", 
        "FEM/drift_tube/mesh.elements", 
        "FEM/drift_tube/mesh.nodes", 
        "FEM/dielectrics.dat",  
        "FEM/drift_tube/drift_tube.result", 
        "cm"
    )
    elm.SetMedium(0, gas)
    elm.SetMedium(1, gas)

    # 3. Sensor y Tracker
    R_anode = 0.002
    sensor = Sensor()
    sensor.AddComponent(elm)
    sensor.SetArea(-2.0, -2.0, -2.0, 2.0, 2.0, 2.0)

    # Instanciamos el Tracker inicial
    track = TrackHeed(sensor)
    
    avalanche = AvalancheMC()
    avalanche.SetSensor(sensor)
    avalanche.SetDistanceSteps(0.002)
    avalanche.EnableMultiplication(True)
    avalanche.EnableAvalancheSizeLimit(1000) 
    avalanche.EnableRKFSteps(True)

    # 4. Configuración del espectro
    fe55_energies = [6403.84, 6390.84, 7058.0]
    weights = [0.45, 0.20, 0.35]

    # Histograma para la versión colimada
    hEspectro = ROOT.TH1F("hEspectro", "Espectro Fe55 Colimado (r=0.2);Electrones;Frecuencia", 100, 0, 500000)

    # 5. Bucle con escritura dinámica y re-intento
    n_eventos = 5000
    print(f"\n--- Iniciando captura de {n_eventos} eventos COLIMADOS (r = 0.2 cm) ---")

    with open("datos_espectro_fe55_5000.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Energia_eV", "Electrones"])
        
        for i in tqdm(range(n_eventos), desc="Progreso Colimado"):
            total_electrons = 0
            
            while total_electrons == 0:
                photon_energy = random.choices(fe55_energies, weights=weights, k=1)[0]
                
                # Haz colimado restrictivo a la zona central limpia (r = 0.2 cm)
                phi = random.uniform(0, 2 * math.pi)
                r = random.uniform(0, 0.8)  
                x0, y0 = r * math.cos(phi), r * math.sin(phi)
                
                nPrimaryElectrons = ctypes.c_int(0)
                track.TransportPhoton(x0, y0, 0.0, 0.0, photon_energy, -x0, -y0, 0.0, nPrimaryElectrons)

                n_primaries = nPrimaryElectrons.value
                for j in range(n_primaries):
                    xe, ye, ze, te = ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0)
                    track.GetElectron(j, xe, ye, ze, te, ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0))
                    
                    avalanche.AvalancheElectron(xe.value, ye.value, ze.value, te.value)
                    
                    nEndpoints = avalanche.GetNumberOfElectronEndpoints()
                    for k in range(nEndpoints):
                        xStart, yStart, zStart, tStart = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
                        xEnd, yEnd, zEnd, tEnd = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
                        status = ctypes.c_int(0)
                        
                        avalanche.GetElectronEndpoint(k, xStart, yStart, zStart, tStart, xEnd, yEnd, zEnd, tEnd, status)
                        
                        if math.sqrt(xEnd.value**2 + yEnd.value**2) <= (R_anode + 0.0005):
                            total_electrons += 1
            
            # Guardar datos en caliente
            writer.writerow([photon_energy, total_electrons])
            f.flush()
            hEspectro.Fill(total_electrons)
            
            # --- SISTEMA COMPATIBLE DE CONTROL DE MEMORIA RAM ---
            # Re-instanciar destruye los buffers acumulados en el heap de C++
            del track
            track = TrackHeed(sensor)
            # Forzar a Python a liberar la memoria inmediatamente
            gc.collect()

    # 6. Guardado final
    cHist = ROOT.TCanvas("cHist", "Espectro", 800, 600)
    hEspectro.SetFillColor(ROOT.kGreen - 3)
    hEspectro.Draw()
    cHist.SaveAs("resolucion_fe55_5000.png")
    print("\nSimulación colimada finalizada con éxito.")

if __name__ == "__main__":
    main()