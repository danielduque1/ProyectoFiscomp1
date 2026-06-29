#!/usr/bin/env python3
import sys
import ROOT

ROOT.gROOT.SetBatch(True)

if ROOT.gSystem.Load("libGarfield") < 0:
    print("[Error] No se pudo cargar libGarfield")
    sys.exit(1)

def main():
    print("=== Generador de Gas de Magboltz - Optimización de Presión y Mezcla ===")
    
    # --- CAMBIO DE ENFOQUE: Incremento de Presión para mejorar resolución ---
    # Pasamos de ~0.95 atm a una presión mayor (ej. 2.0 bar) para comprimir la difusión
    # y mejorar de forma física el ancho de los picos. Puedes ajustar este valor.
    presion_bar = 2.0  
    presion_torr = presion_bar * 750.062  # Conversión automática a Torr para Magboltz
    temperatura_k = 293.15                 

    gas = ROOT.Garfield.MediumMagboltz()
    
    # --- COMPOSICIÓN ACTUALIZADA ---
    # Volvemos a tu mezcla del Drift Tube que está operando sin problemas
    gas.SetComposition("ar", 70.0, "co2", 30.0)
    
    gas.SetPressure(presion_torr)
    gas.SetTemperature(temperatura_k)
    
    # Rango de energía dinámico para asegurar cálculo óptimo de estados excitados
    gas.SetMaxElectronEnergy(40.0)

    # --- REJILLA DE CAMPO ELÉCTRICO PARA DRIFT TUBE ---
    # En un tubo de deriva los campos van desde la zona exterior baja (~10 V/cm) 
    # hasta campos moderadamente altos cerca del hilo conductor (~20,000 V/cm)
    nE = 20           
    emin = 10.0       # V/cm (Umbral inferior reducido para capturar el volumen del tubo)
    emax = 30000.0    # V/cm (Umbral superior calibrado para el ánodo del hilo)
    useLog = True     
    gas.SetFieldGrid(emin, emax, nE, useLog)

    # Configuración de colisiones estándar para convergencia rápida y precisa
    ncoll = 2 
    
    # Formateo del nombre del archivo reflejando la composición y la nueva presión
    nombre_archivo = f"ar_70_co2_30_{int(presion_bar)}bar.gas"
    print(f"\nIniciando Magboltz para calcular {nE} puntos a {presion_bar} bar...")
    print(f"Mezcla: Ar/CO2 (70/30) @ {presion_torr:.2f} Torr, {temperatura_k} K.")
    print("Corriendo... Esto tardará alrededor de 2 a 4 minutos...")
    
    gas.GenerateGasTable(ncoll)
    gas.WriteGasFile(nombre_archivo)
    
    print(f"\n[Éxito] Nueva tabla de gas guardada correctamente como: '{nombre_archivo}'")

if __name__ == "__main__":
    main()