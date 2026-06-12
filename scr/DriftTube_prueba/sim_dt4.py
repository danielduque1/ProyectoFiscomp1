import sys
import math
import csv
import ROOT

import pandas as pd
from pathlib import Path
import Garfield

if ROOT.gSystem.Load("libGarfield") < 0:
    print("[Error] No se pudo cargar libGarfield")
    sys.exit(1)

# =========================================================================
# 1. CONFIGURACIÓN DEL GAS Y CAMPO ELÉCTRICO FEM
# =========================================================================
gas = ROOT.Garfield.MediumMagboltz()
gas.LoadGasFile('ar_93_co2_7_3bar.gas')
gas.LoadIonMobility('/home/daniel/garfield/install/share/Garfield/Data/IonMobility_Ar+_Ar.txt')
gas.EnableDrift()

# CORRECCIÓN DE PALABRAS CLAVE: Uso de "constant" y "exponential" según la especificación de C++
gas.SetExtrapolationMethodTownsend("constant", "exponential")
gas.SetExtrapolationMethodAttachment("constant", "constant")

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
# 2. DEFINICIÓN DEL DETECTOR Y DINÁMICA DE AVALANCHA
# =========================================================================
R_tube = 1.0     
R_anode = 0.002  
axis_lim = 1.2

sensor = ROOT.Garfield.Sensor()
sensor.AddComponent(elm)
sensor.SetArea(-axis_lim, -axis_lim, -axis_lim, axis_lim, axis_lim, axis_lim)

track = ROOT.Garfield.TrackHeed(sensor)
track.SetParticle('muon')

drift = ROOT.Garfield.DriftLineRKF(sensor)

ganancia_media = 1_000.0
drift.SetGainFluctuationsPolya(0.0, ganancia_media)

# =========================================================================
# 3. GEOMETRÍA DE LA TRAYECTORIA Y PREPARACIÓN DE DATOS
# =========================================================================
rTrack = 0.3
x0 = rTrack
y0 = -math.sqrt(R_tube**2 - rTrack**2) + 0.001

csv_name = "muon_spectrum_sea_level"
here = Path(__file__).resolve()
repo_root = here.parents[2]
csv_path = repo_root / "data" / "processed" / f"{csv_name}.csv"
if not csv_path.exists():
    csv_path = Path.cwd() / "data" / "processed" / f"{csv_name}.csv"

df = pd.read_csv(csv_path)

names = df["Name"].tolist()
energies = df["Energy_eV"].values
probabilities = df["Probability"].values

Eventos_totales = 1000

# =========================================================================
# 4. BUCLE DE EXCITACIONES CON MULTIPLICACIÓN MACROSCÓPICA (MODO SILENCIOSO)
# =========================================================================
for j in range(len(names)):
    nombre = names[j]
    energia_eV = energies[j]
    n_eventos = int(Eventos_totales * probabilities[j])
    
    if n_eventos == 0:
        print(f"\nSaltando componente {nombre} debido a estadística nula.")
        continue

    hist_id = f"hConteos_{nombre}"
    hist_title = f"Espectro {nombre};Electrones Finales;Frecuencia"
    hConteos = ROOT.TH1F(str(hist_id), str(hist_title), 70, 0, 20.e6)
    
    registro_conteos = []

    print(f"\n--- Ejecutando Componente: {nombre} ({n_eventos} Eventos) ---")
    track.SetEnergy(energia_eV)

    for i in range(n_eventos):
        track.DisablePlotting()
        drift.DisablePlotting()

        track.NewTrack(x0, y0, 0.0, 0.0, 0.0, 1.0, 0.0)
        
        electrones_recolectados_evento = 0
        
        for cluster in track.GetClusters():
            for electron in cluster.electrons:
                status = drift.DriftElectron(electron.x, electron.y, electron.z, electron.t)
                if status:
                    electrones_recolectados_evento += drift.GetGain()
                    
        hConteos.Fill(electrones_recolectados_evento)
        registro_conteos.append(electrones_recolectados_evento)
        
        if (i + 1) % 50 == 0:
            print(f"   -> Procesados {i + 1}/{n_eventos} eventos...")

    # =========================================================================
    # 5. EXPORTACIÓN A CSV
    # =========================================================================
    print("Exportando datos a CSV...")
    out_dir = repo_root / "data" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_output_path = out_dir / f"linea_{nombre}_{int(energia_eV)}.csv"

    with open(csv_output_path, mode="w", newline="") as archivo_csv:
        escritor = csv.writer(archivo_csv)
        escritor.writerow(["Evento", "Electrones_Finales_Anodo"])
        for idx, conteo in enumerate(registro_conteos):
            escritor.writerow([idx + 1, conteo])
    print(f"Archivo '{csv_output_path.name}' guardado exitosamente.")

print("\n======================================================")
print("Simulación headless finalizada. Todos los CSVs generados.")
print("======================================================")