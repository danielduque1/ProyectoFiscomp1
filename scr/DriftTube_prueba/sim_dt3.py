import sys
import math
import queue
import threading
import time
import csv
import ROOT

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

# ACTIVACIÓN DE LA AVALANCHA: 
# Parámetros estándar: theta = 0.0 (Distribución Furry/Exponencial para campos altos)
# Ganancia media típica de un MDT = 20,000 electrones secundarios por primario
ganancia_media = 20000.0
drift.SetGainFluctuationsPolya(0.0, ganancia_media)

viewDrift = ROOT.Garfield.ViewDrift()
viewDrift.SetArea(-axis_lim, -axis_lim, -axis_lim, axis_lim, axis_lim, axis_lim)

# =========================================================================
# 3. GEOMETRÍA DE LA TRAYECTORIA Y PREPARACIÓN DE DATOS (ESCALA AMPLIADA)
# =========================================================================
rTrack = 0.3
x0 = rTrack
y0 = -math.sqrt(R_tube**2 - rTrack**2) + 0.001

n_eventos = 100
energia_muon = 170.e9

# MODIFICACIÓN DE RANGO: Al multiplicar por ~20,000, los límites del histograma 
# deben expandirse drásticamente. Mapeamos de 0 a 20 Millones de electrones finales.
hConteos = ROOT.TH1F("hConteos", "Carga Recolectada en el Anodo;Numero de Electrones Finales;Frecuencia", 70, 0, 20.e6)

registro_conteos = []

# =========================================================================
# 4. BUCLE DE EXCITACIONES CON MULTIPLICACIÓN MACROSCÓPICA
# =========================================================================
print(f"\n--- Iniciando simulaciones con Avalancha Activa ({n_eventos} Eventos) ---")
track.SetEnergy(energia_muon)

for i in range(n_eventos):
    if i == 0:
        track.EnablePlotting(viewDrift)
        drift.EnablePlotting(viewDrift)
    else:
        track.DisablePlotting()
        drift.DisablePlotting()

    track.NewTrack(x0, y0, 0.0, 0.0, 0.0, 1.0, 0.0)
    
    electrones_recolectados_evento = 0
    
    for cluster in track.GetClusters():
        for electron in cluster.electrons:
            # Simulamos la deriva del electrón primario hacia el ánodo
            status = drift.DriftElectron(electron.x, electron.y, electron.z, electron.t)
            
            # Si el electrón llega con éxito al ánodo, extraemos el tamaño de su avalancha
            if status:
                # GetGain() devuelve el número de electrones secundarios generados por este primario
                electrones_recolectados_evento += drift.GetGain()
                
    # Llenar el histograma con la carga final real retenida
    hConteos.Fill(electrones_recolectados_evento)
    registro_conteos.append(electrones_recolectados_evento)
    
    if (i + 1) % 10 == 0:
        print(f"Completados {i + 1}/{n_eventos} eventos...")

# =========================================================================
# 5. EXPORTACIÓN A CSV (RECOLECCIÓN FINAL)
# =========================================================================
print("\nExportando datos a CSV...")
with open("/home/daniel/Workspace/Repositorios/ProyectoFiscomp1/data/outputs/carga_recolectada_anodo_170GeV.csv", mode="w", newline="") as archivo_csv:
    escritor = csv.writer(archivo_csv)
    escritor.writerow(["Evento", "Electrones_Finales_Anodo"])
    for i, conteo in enumerate(registro_conteos):
        escritor.writerow([i + 1, conteo])
print("Archivo 'carga_recolectada_anodo_170GeV.csv' guardado exitosamente.")

# =========================================================================
# 6. DIBUJO ESTRUCTURADO
# =========================================================================
cGeom = ROOT.TCanvas("cGeom", "Evento de Control - Traza y Deriva", 700, 700)
cGeom.cd()
viewDrift.SetCanvas(cGeom)
viewDrift.Plot(True, True)

catodo = ROOT.TEllipse(0, 0, R_tube, R_tube)
catodo.SetLineColor(ROOT.kBlack)
catodo.SetLineWidth(2)
catodo.SetFillStyle(0)
catodo.Draw("")

anodo = ROOT.TEllipse(0, 0, R_anode*5, R_anode*5)
anodo.SetLineColor(ROOT.kRed)
anodo.SetFillColor(ROOT.kRed)
anodo.Draw("")
cGeom.Update()

cHist = ROOT.TCanvas("cHist", "Histograma de Carga Final (100 Muones)", 700, 500)
cHist.cd()
hConteos.SetFillColor(ROOT.kGreen - 6) # Cambiado a verde para diferenciarlo del anterior
hConteos.SetLineColor(ROOT.kGreen + 2)
hConteos.Draw()
cHist.Update()

# =========================================================================
# 7. SISTEMA DE CONTROL ASINCRÓNICO
# =========================================================================
commands = queue.Queue()

def read_commands():
    while True:
        try:
            command = input("\n[Gráficos listos] Ingrese 'q' para terminar: ").strip().lower()
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
cHist.Close()