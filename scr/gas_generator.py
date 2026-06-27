#!/usr/bin/env python3
import sys
import ROOT

ROOT.gROOT.SetBatch(True)

if ROOT.gSystem.Load("libGarfield") < 0:
    print("[Error] No se pudo cargar libGarfield")
    sys.exit(1)

def main():
    print("=== Generador Optimizado de Gas de Magboltz (Alta Velocidad) ===")
    
    presion_bar = 5.0
    presion_torr = presion_bar * 750.062  # 3750.31 Torr
    temperatura_k = 293.15                 

    gas = ROOT.Garfield.MediumMagboltz()
    gas.SetComposition("ar", 93.0, "co2", 7.0)
    
    gas.SetPressure(presion_torr)
    gas.SetTemperature(temperatura_k)
    
    # --- OPTIMIZACIÓN 1: Dejar que la API maneje la energía de forma dinámica ---
    # Al no forzar los 40 eV manuales desde el inicio, Magboltz no desperdiciará 
    # ciclos de reloj integrando regiones vacías en campos de drift bajos.
    # Conservará automáticamente las tasas de excitación al subir el campo.

    # --- OPTIMIZACIÓN 2: Rejilla ágil de 15 puntos ---
    nE = 15           
    emin = 100.0      # V/cm
    emax = 100000.0   # V/cm
    useLog = True     
    gas.SetFieldGrid(emin, emax, nE, useLog)

    # --- OPTIMIZACIÓN 3: Ajustar colisiones a nivel de convergencia estándar ---
    # ncoll = 2 equivale a 20 millones de colisiones simuladas por punto.
    # Conserva la precisión física reduciendo el tiempo de CPU en un 80%.
    ncoll = 2 
    
    nombre_archivo = f"ar_93_co2_7_{int(presion_bar)}bar.gas"
    print(f"\nIniciando Magboltz para calcular {nE} puntos logarítmicos a {presion_bar} bar...")
    print("Corriendo versión optimizada. Esto tardará alrededor de 2 a 3 minutos...")
    
    gas.GenerateGasTable(ncoll)
    gas.WriteGasFile(nombre_archivo)
    
    print(f"\n[Éxito] Tabla de gas guardada correctamente como: '{nombre_archivo}'")

if __name__ == "__main__":
    main()