#!/usr/bin/env python3
import sys
import math
import random
import ctypes
import csv
import gc
import ROOT
from tqdm import tqdm

# Configurar ROOT en modo batch (Esencial para ejecuciones limpias en servidores o terminales)
ROOT.gROOT.SetBatch(True)

if ROOT.gSystem.Load("libGarfield") < 0:
    print("[Error] No se pudo cargar libGarfield")
    sys.exit(1)

MediumMagboltz = ROOT.Garfield.MediumMagboltz
ComponentElmer = ROOT.Garfield.ComponentElmer
Sensor         = ROOT.Garfield.Sensor
TrackHeed      = ROOT.Garfield.TrackHeed
AvalancheMC    = ROOT.Garfield.AvalancheMC

def main():
    # =========================================================================
    # 1. SELECCIÓN DE FUENTE RADIACTIVA (Fijar en True para cambiar al Am-241)
    # =========================================================================
    USAR_AMERICIO = False 

    if USAR_AMERICIO:
        print("=== CONFIGURACIÓN DE PRODUCCIÓN: AMERICIO-241 (59.5 keV) ===")
        energies = [59540.9, 26344.6, 13900.0]  # eV
        weights  = [0.359, 0.024, 0.42]
        max_val_histograma = 2500  # Escala adaptada para la gran cascada del Americio
    else:
        print("=== CONFIGURACIÓN DE PRODUCCIÓN: HIERRO-55 (5.9 keV) ===")
        energies = [6403.84, 6390.84, 7058.0]   # eV (Líneas de rayos X característicos)
        weights  = [0.5972, 0.3021, 0.1007]
        max_val_histograma = 400   # Escala adaptada para el Hierro

    # =========================================================================
    # 2. CONFIGURACIÓN DEL MEDIO GASEOSO A ALTA PRESIÓN (5 BAR)
    # =========================================================================
    gas = MediumMagboltz()
    if not gas.LoadGasFile("ar_93_co2_7_5bar.gas"):
        print("[Error] No se encontró el archivo de gas optimizado a 5 bar.")
        sys.exit(1)
    
    # Activar el Efecto Penning para la ionización primaria de Heed
    gas.EnablePenningTransfer(0.12, 0.0, "ar")

    # =========================================================================
    # 3. CARGA DEL MAPA DE CAMPOS ELECTROSTÁTICOS DE ELMER
    # =========================================================================
    elm = ComponentElmer()
    elm.Initialise(
        "FEM/gem/mesh.header",
        "FEM/gem/mesh.elements",
        "FEM/gem/mesh.nodes",
        "FEM/gem/dielectrics.dat",
        "FEM/gem/gem.result",
        "mm"
    )
    elm.SetMedium(0, gas) # Mapeo al índice material 0 (Gas activo)
    elm.EnablePeriodicityX()
    elm.EnablePeriodicityY()

    # Cálculo de los límites reales de la celda unitaria basados en tu pitch (0.140 mm)
    pitch = 0.140
    Lx = pitch / 2.0
    Ly = (math.sqrt(3.0) * pitch) / 2.0
    
    # Límites físicos en centímetros nativos de Garfield++
    Z_colector_limite = -0.095  # Umbral para el plano del Ánodo (z = -0.95 mm)
    Z_cobre_superior  = 0.0025  # Frontera geométrica superior de la GEM (z = 0.025 mm)

    # =========================================================================
    # 4. CONFIGURACIÓN DEL SENSOR GLOBAL
    # =========================================================================
    sensor = Sensor()
    sensor.AddComponent(elm)
    sensor.SetArea(-0.001, -0.001, -0.105, Lx/10.0 + 0.001, Ly/10.0 + 0.001, 0.105)

    # Configurar parámetros microscópicos de transporte para la avalancha
    avalanche = AvalancheMC()
    avalanche.SetSensor(sensor)
    avalanche.SetDistanceSteps(0.0005)  # Pasos finos de 5 micras
    avalanche.EnableMultiplication(True)
    avalanche.EnableAvalancheSizeLimit(10000) # Límite amplio para evitar truncamientos
    avalanche.EnableRKFSteps(True)

    # Histograma nativo de ROOT para graficar la resolución energética
    hEspectro = ROOT.TH1F("hEspectro", f"Resolucion Energetica GEM 3D;Electrones Colectados (Anodo);Frecuencia", 80, 0, max_val_histograma)

    n_eventos_utiles = 500
    print(f"\nIniciando la acumulación estricta de {n_eventos_utiles} eventos de simulación...\n")

    track = TrackHeed(sensor)

    # Crear archivo CSV de salida para almacenar los espectros crudos
    with open("espectro_gem_produccion.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Energia_Foton_eV", "Electrones_Colectados_Anodo"])
        
        # Bucle principal controlado con barra de progreso tqdm
        for i in tqdm(range(n_eventos_utiles), desc="Procesando Eventos GEM"):
            electrones_totales_evento = 0
            interaccion_valida = False
            n_primarios = 0
            
            # Bucle estocástico controlado: Forzar disparos hasta lograr absorción útil en el drift superior
            while not interaccion_valida:
                photon_energy = random.choices(energies, weights=weights, k=1)[0]
                
                # Muestreo espacial aleatorio uniforme en X e Y sobre la cara de la celda
                x0_cm = random.uniform(0.0, Lx / 10.0)
                y0_cm = random.uniform(0.0, Ly / 10.0)
                z0_cm = 0.095  # Disparo en la cima del Gap de Drift (z = 0.95 mm)
                
                dx, dy, dz = 0.0, 0.0, -1.0  # Vector apuntando verticalmente hacia abajo
                nPrimaryElectrons = ctypes.c_int(0)
                
                track.TransportPhoton(x0_cm, y0_cm, z0_cm, 0.0, photon_energy, dx, dy, dz, nPrimaryElectrons)
                
                if nPrimaryElectrons.value > 0:
                    # Analizar la coordenada de nacimiento real del primer electrón de la cascada
                    xe, ye, ze, te = ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0)
                    track.GetElectron(0, xe, ye, ze, te, ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0))
                    
                    # FILTRO FÍSICO: La fotoabsorción debe ocurrir estrictamente arriba de la GEM (en la zona de drift)
                    if ze.value > Z_cobre_superior:
                        interaccion_valida = True
                        n_primarios = nPrimaryElectrons.value
            
            # Simular de forma consecutiva la trayectoria de cada electrón primario j de la cascada
            for j in range(n_primarios):
                xe, ye, ze, te = ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0)
                track.GetElectron(j, xe, ye, ze, te, ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0))
                
                avalanche.AvalancheElectron(xe.value, ye.value, ze.value, te.value)
                
                # Contar cuántos descendientes de esta rama alcanzaron el plano de lectura final
                nEndpoints = avalanche.GetNumberOfElectronEndpoints()
                for k in range(nEndpoints):
                    xStart, yStart, zStart, tStart = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
                    xEnd, yEnd, zEnd, tEnd = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
                    status = ctypes.c_int(0)
                    
                    avalanche.GetElectronEndpoint(k, xStart, yStart, zStart, tStart, xEnd, yEnd, zEnd, tEnd, status)
                    
                    # Condición de registro geométrico en el ánodo colector inferior
                    if zEnd.value <= Z_colector_limite:
                        electrones_totales_evento += 1
            
            # Escribir el resultado del evento en el archivo y rellenar el histograma
            writer.writerow([photon_energy, electrones_totales_evento])
            f.flush()
            hEspectro.Fill(electrones_totales_evento)
            
            # Liberación del Heap de memoria para mitigar fugas de RAM de PyROOT en bucles largos 3D
            del track
            track = TrackHeed(sensor)
            gc.collect()

    # Guardar y formatear el gráfico final de resolución espectral
    c1 = ROOT.TCanvas("c1", "Espectro de Resolucion Energetica", 800, 600)
    hEspectro.SetFillColor(ROOT.kOrange + 7)
    hEspectro.SetLineColor(ROOT.kBlack)
    hEspectro.Draw()
    c1.SaveAs("espectro_resolucion_gem.png")
    print("\n[Éxito Total] Simulación de producción finalizada. Histograma guardado en 'espectro_resolucion_gem.png'.")

if __name__ == "__main__":
    main()