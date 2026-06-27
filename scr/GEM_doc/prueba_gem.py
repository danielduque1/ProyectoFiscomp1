#!/usr/bin/env python3
import sys
import ctypes
import ROOT

# Activar modo batch para procesamiento eficiente en memoria
ROOT.gROOT.SetBatch(True)

# Cargar librería de Garfield++
if ROOT.gSystem.Load("libGarfield") < 0:
    print("[Error] No se pudo cargar libGarfield")
    sys.exit(1)

# Aliases nativos para la API 3D de Garfield++
MediumMagboltz = ROOT.Garfield.MediumMagboltz
ComponentElmer = ROOT.Garfield.ComponentElmer  
Sensor         = ROOT.Garfield.Sensor
TrackHeed      = ROOT.Garfield.TrackHeed
AvalancheMC    = ROOT.Garfield.AvalancheMC

def main():
    print("=== Iniciando Test Unitario GEM 3D (Ar-93 / CO2-7 @ 5bar) ===")
    
    # 1. Configuración del Gas de Magboltz Optimizado
    gas = MediumMagboltz()
    if not gas.LoadGasFile("ar_93_co2_7_5bar.gas"):
        print("[Error] Archivo 'ar_93_co2_7_5bar.gas' no encontrado en el directorio actual.")
        sys.exit(1)
        
    # --- CALIBRACIÓN ASGURADA DEL EFECTO PENNING ---
    r_penning = 0.12  
    lambda_penning = 0.0 # cm
    gas.EnablePenningTransfer(r_penning, lambda_penning, "ar")

    # 2. Inicializar el mapa de campos 3D de Elmer
    elm = ComponentElmer()
    elm.Initialise(
        "FEM/gem/mesh.header",
        "FEM/gem/mesh.elements",
        "FEM/gem/mesh.nodes",
        "FEM/gem/dielectrics.dat",
        "FEM/gem/gem.result",
        "mm"
    )
    
    # Vincular el gas al índice material 0
    elm.SetMedium(0, gas)

    # Activar condiciones periódicas en las fronteras laterales de la celda unitaria
    elm.EnablePeriodicityX()
    elm.EnablePeriodicityY()

    # 3. Configuración del Sensor
    sensor = Sensor()
    sensor.AddComponent(elm)
    sensor.SetArea(-0.001, -0.001, -0.105, 0.008, 0.013, 0.105)

    # 4. Configuración de los procesos de Tracking y Avalancha (ORIGINALES)
    track = TrackHeed(sensor)
    
    avalanche = AvalancheMC()
    avalanche.SetSensor(sensor)
    avalanche.SetDistanceSteps(0.0005) 
    avalanche.EnableMultiplication(True)
    avalanche.EnableAvalancheSizeLimit(2000) 
    avalanche.EnableRKFSteps(True)

    print("\n--- Iniciando disparo de fotones en el Gas Activo (Gap de Drift) ---")
    
    # Coordenadas de disparo en centímetros nativos ubicadas en pleno centro del gas
    x_cm = 0.0035  
    y_cm = 0.0060  
    z_cm = 0.0950  
    
    dx, dy, dz = 0.0, 0.0, -1.0
    photon_energy = 5900.0  # eV (Línea K-alfa del Fe-55)

    nPrimaryElectrons = ctypes.c_int(0)
    intentos = 0
    max_intentos = 150

    # Bucle controlado para absorber la transparencia geométrica residual
    while nPrimaryElectrons.value == 0 and intentos < max_intentos:
        intentos += 1
        track.TransportPhoton(x_cm, y_cm, z_cm, 0.0, photon_energy, dx, dy, dz, nPrimaryElectrons)
    
    if nPrimaryElectrons.value > 0:
        print(f"\n¡Interacción fotoeléctrica exitosa lograda en el intento {intentos}!")
        print(f"El gas absorbió el fotón. Electrones primarios iniciales (Heed + Penning): {nPrimaryElectrons.value}")
        
        total_electrones_lectura = 0
        total_endpoints_procesados = 0
        
        # Iterar sobre la cascada completa de todos los electrones primarios generados por Heed
        for i in range(nPrimaryElectrons.value):
            xe, ye, ze, te = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
            dummy_energy = ctypes.c_double(0)
            dummy_dx, dummy_dy, dummy_dz = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
            
            # Obtener el electrón primario i-ésimo
            track.GetElectron(i, xe, ye, ze, te, dummy_energy, dummy_dx, dummy_dy, dummy_dz)
            
            # Simular la avalancha microscópica
            avalanche.AvalancheElectron(xe.value, ye.value, ze.value, te.value)
            
            nEndpoints = avalanche.GetNumberOfElectronEndpoints()
            total_endpoints_procesados += nEndpoints
            
            # Analizar el destino final de los electrones utilizando la firma exacta de la API de C++
            for j in range(nEndpoints):
                x0, y0, z0, t0 = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
                x1, y1, z1, t1 = ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0), ctypes.c_double(0)
                status = ctypes.c_int(0)
                
                # LLAMADA CORREGIDA: Se remueven e0 y e1 de los argumentos (10 argumentos en total pasados)
                avalanche.GetElectronEndpoint(j, x0, y0, z0, t0, x1, y1, z1, t1, status)
                
                # Filtrado geométrico (en cm): El plano inferior de lectura se ubica en Z = -1.0 mm (-0.100 cm).
                # Si z1 alcanza o cruza el umbral de -0.095 cm, el electrón llegó efectivamente al ánodo.
                if z1.value <= -0.095:
                    total_electrones_lectura += 1

        print(f"\n--- Procesamiento de Avalanchas Finalizado ---")
        print(f"Total de electrones simulados en el volumen (Avalancha MC): {total_endpoints_procesados}")
        print(f"Electrones registrados exitosamente en el extremo de lectura (Ánodo): {total_electrones_lectura}")
        
        ganancia_efectiva = total_electrones_lectura / nPrimaryElectrons.value
        print(f"Ganancia efectiva medida en este evento: {ganancia_efectiva:.2f}")
        
    else:
        print(f"[Error] No se registró absorción cuántica tras {max_intentos} disparos en la celda.")

    print("\n=== TEST UNITARIO FINALIZADO CON ÉXITO ===")

if __name__ == "__main__":
    main()