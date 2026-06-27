#!/usr/bin/env python3
import sys
import math
import random
import ctypes
import csv
import gc
import ROOT
import Garfield

# 1. Configuración de ROOT y carga de Librería
ROOT.gROOT.SetBatch(True)

if ROOT.gSystem.Load("libGarfield") < 0:
    print("[Error] No se pudo cargar libGarfield")
    sys.exit(1)

import Garfield

# 2. Carga del mapa de campos de ANSYS (Estático)
fm = ROOT.Garfield.ComponentAnsys123()
fm.Initialise("ELIST.lis", "NLIST.lis", "MPLIST.lis", "PRNSOL.lis", "mm")
fm.EnableMirrorPeriodicityX()
fm.EnableMirrorPeriodicityY()

# Dimensiones de la celda GEM [cm]
pitch = 0.014

# 3. Configuración del Gas (Magboltz)
gas = ROOT.Garfield.MediumMagboltz("ar", 80., "co2", 20.)
gas.SetTemperature(293.15)
gas.SetPressure(760.)
gas.Initialise(True)

# Eficiencia de transferencia Penning
rPenning = 0.51
gas.EnablePenningTransfer(rPenning, 0., "ar")
gas.LoadIonMobility('IonMobility_Ar+_Ar.txt')
 
fm.SetGas(gas)

# 4. Ensamblaje del Sensor (CORREGIDO: Expandido al límite real del mapa ANSYS, ±1.0 mm = ±0.1 cm)
sensor = ROOT.Garfield.Sensor()
sensor.AddComponent(fm)
sensor.SetArea(-5 * pitch, -5 * pitch, -0.1, 5 * pitch,  5 * pitch, 0.1)

# Rastreador Heed para fotones de Fe55
track = ROOT.Garfield.TrackHeed(sensor)

# Avalancha microscópica
aval = ROOT.Garfield.AvalancheMicroscopic(sensor)

# 5. Configuración del espectro del Hierro-55
fe55_energies = [6403.84, 6390.84, 7058.0]
weights = [0.5, 0.15, 0.35]

# Histograma para guardar el espectro final
hEspectro = ROOT.TH1F("hEspectro", "Espectro Fe55 en GEM Corregido;Electrones Colectados;Frecuencia", 100, 0, 18000)

nEvents = 150  # Se recomienda subir a 300-500 para ver la separación estadística clara
print(f"\n--- Iniciando captura de {nEvents} eventos en GEM (Contención de Track Completa) ---")

FACTOR_GANANCIA_VIRTUAL = 12.0  

with open("datos_espectro_fe55_gem_corregido.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Energia_eV", "Electrones"])
    
    for i in range(nEvents):
        total_electrons = 0
        print(f"Procesando evento {i+1}/{nEvents}...")
        
        while total_electrons == 0:
            photon_energy = random.choices(fe55_energies, weights=weights, k=1)[0]
            
            # Colimación central en el orificio
            radio_colimacion = 0.0025  
            phi = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, radio_colimacion)
            
            x0 = r * math.cos(phi)
            y0 = r * math.sin(phi)
            
            # --- MODIFICACIÓN CRÍTICA: PUNTO DE INYECCIÓN ---
            # Colocamos el inicio del fotón en z = 0.09 cm (cerca del techo de la deriva a 1 mm).
            # Esto le otorga al fotoelectrón el espacio suficiente para frenarse por completo en el gas.
            z0 = 0.09  
            
            nPrimaryElectrons = ctypes.c_int(0)
            track.TransportPhoton(x0, y0, z0, 0.0, photon_energy, 0.0, 0.0, -1.0, nPrimaryElectrons)
            
            n_primaries = nPrimaryElectrons.value
            electrones_sobrevivientes = 0
            
            for j in range(n_primaries):
                xe, ye, ze, te = ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0)
                ee, dx, dy, dz = ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0), ctypes.c_double(0.0)
                track.GetElectron(j, xe, ye, ze, te, ee, dx, dy, dz)
                
                # Simular avalancha microscópica
                aval.AvalancheElectron(xe.value, ye.value, ze.value, te.value, ee.value, dx.value, dy.value, dz.value)
                
                nEndpoints = aval.GetNumberOfElectronEndpoints()
                for k in range(nEndpoints):
                    xStart, yStart, zStart, tStart = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
                    xEnd, yEnd, zEnd, tEnd = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
                    eStart, eEnd = ctypes.c_double(0), ctypes.c_double(0)
                    status = ctypes.c_int(0)
                    
                    aval.GetElectronEndpoint(k, xStart, yStart, zStart, tStart, eStart, 
                                             xEnd, yEnd, zEnd, tEnd, eEnd, status)
                    
                    # El canal inferior termina cerca de z = -0.003 cm; cualquier electrón por debajo cuenta como colectado
                    if zEnd.value < -0.004:
                        electrones_sobrevivientes += 1
            
            # Escalamiento estocástico de ganancia
            if electrones_sobrevivientes > 0:
                factor_fluctuante = random.gauss(FACTOR_GANANCIA_VIRTUAL, FACTOR_GANANCIA_VIRTUAL * 0.05)
                total_electrons = int(electrones_sobrevivientes * max(1.0, factor_fluctuante))
        
        # Guardar datos procesados
        writer.writerow([photon_energy, total_electrons])
        f.flush()
        hEspectro.Fill(total_electrons)
        
        # Limpieza de memoria RAM C++
        del track
        track = ROOT.Garfield.TrackHeed(sensor)
        gc.collect()

# 6. Generación del gráfico del Espectro
cHist = ROOT.TCanvas("cHist", "Espectro Optimizado", 800, 600)
hEspectro.SetFillColor(ROOT.kOrange + 7)
hEspectro.SetLineColor(ROOT.kBlack)
hEspectro.Draw()

# Ajuste Gaussiano para encontrar la resolución del pico principal
hEspectro.Fit("gaus", "Q")

cHist.SaveAs("resolucion_fe55_gem_campana.png")
print("\nSimulación finalizada exitosamente. Archivo 'datos_espectro_fe55_gem_corregido.csv' generado.")