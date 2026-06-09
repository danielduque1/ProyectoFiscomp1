import ROOT
import math
import os
import Garfield

# 1. Configuración del Medio Gaseoso (Ar/CO2 93/7)
# Asegúrate de tener generado el archivo .gas correspondiente a tu mezcla 93/7
gas = ROOT.Garfield.MediumMagboltz()
gas_file = "ar_93_co2_7_3bar.gas"

if os.path.exists(gas_file):
    gas.LoadGasFile(gas_file)
else:
    raise FileNotFoundError(f"Falta el archivo de gas {gas_file}. Genéralo con Magboltz si es necesario.")

# Cargar movilidad de iones para los cálculos de tiempo de tránsito/corrientes
# Puedes usar una aproximación estándar o un archivo de movilidad estructurado
gas.LoadIonMobility("IonMobility_Ar+_Ar.txt") 

# 2. Importar el Campo Electrostático desde Elmer FEM
elm = ROOT.Garfield.ComponentElmer2d(
    "FEM/drift_tube/mesh.header",
    "FEM/drift_tube/mesh.elements",
    "FEM/drift_tube/mesh.nodes",
    "FEM/dielectrics.dat",
    "FEM/drift_tube/drift_tube.result",
    "cm" # Unidades de tu malla en Gmsh
)

# Asociar el medio gaseoso al volumen del gas (Material 1 en Elmer es indexado como 0 en el vector de Garfield)
elm.SetMedium(0, gas)

# =========================================================================
# 3. CREAR EL SENSOR Y CONFIGURAR SEÑALES (CORRIENTES INDUCIDAS)
# =========================================================================
sensor = ROOT.Garfield.Sensor()
sensor.AddComponent(elm)

# Asociar el peso de inducción a la frontera física del ánodo (BC 1 en tu .sif)
sensor.AddElectrode(elm, "Anode_Wire")

# Configurar la ventana de tiempo para registrar las corrientes [en nanosegundos]
t_step = 0.5      # Paso de tiempo en ns
t_min = -0.5 * t_step
n_bins = 1000     # Canales del osciloscopio virtual
sensor.SetTimeWindow(t_min, t_step, n_bins)

# =========================================================================
# 4. CONFIGURAR SOLVERS DE TRANSPORTE Y VISUALIZACIÓN DE AVALANCHAS
# =========================================================================
# Configurar Heed para la ionización primaria por muones
track = ROOT.Garfield.TrackHeed(sensor)
track.SetParticle("muon")

# Configurar Runge-Kutta-Fehlberg para las líneas de deriva y avalanchas
drift = ROOT.Garfield.DriftLineRKF(sensor)
# Activar fluctuaciones de ganancia (Simulación del mecanismo de Townsend / Polya)
drift.SetGainFluctuationsPolya(0.6, 100.0) 

# --- Inicialización del Canvas y Visor para las Líneas de Deriva ---
c_drift = ROOT.TCanvas("c_drift", "Visualizacion de la Avalancha", 700, 700)
view_drift = ROOT.Garfield.ViewDrift()
view_drift.SetCanvas(c_drift)

# Enlazar solvers al visor gráfico
drift.EnablePlotting(view_drift)
track.EnablePlotting(view_drift)

# =========================================================================
# 5. FUNCIÓN CORE: SIMULACIÓN DE UN EVENTO (DISPARO DE PARTÍCULA)
# =========================================================================
def simular_evento(energia_gev, x_impacto, flag_graficar_evento=False):
    # Convertir energía de GeV a eV para TrackHeed
    track.SetEnergy(energia_gev * 1e9)
    
    # Trayectoria vertical (eje Y) que cruza el tubo en la coordenada X dada
    # Parámetros: x0, y0, z0, t0, dx, dy, dz, ...
    track.NewTrack(x_impacto, -0.99, 0, 0, 0, 1, 0, 0, 0)
    
    total_electrones_primarios = 0
    
    # Limpiar el búfer de señales del sensor antes de este evento
    sensor.ClearSignal()

    # Iterar sobre los clusters de ionización generados por el muón
    for cluster in track.GetClusters():
        total_electrones_primarios += len(cluster.electrons)
        
        # Transportar cada electrón secundario hacia el ánodo
        for electron in cluster.electrons:
            # Simula la deriva e integra la amplificación/Townsend en el camino
            drift.DriftElectron(electron.x, electron.y, electron.z, electron.t)
            
    # Si se solicita, renderizar el mapa espacial de este evento en específico
    if flag_graficar_evento:
        c_drift.cd()
        view_drift.Plot()
        c_drift.Update()
        c_drift.SaveAs(f"avalancha_{energia_gev}GeV.png")
        
    return total_electrones_primarios

# =========================================================================
# 6. BUCLE PRINCIPAL: BARRIDO DE ENERGÍAS E HISTOGRAMAS
# =========================================================================
energies = [1.0, 10.0, 50.0]  # Energías a evaluar en GeV
histogramas = {}
eventos_por_energia = 50       # Número de disparos por cada energía

for eng in energies:
    name = f"h_counts_{eng}GeV"
    title = f"Distribucion de Carga - {eng} GeV;Electrones Primarios;Conteos"
    # Histograma de ROOT: 80 bins entre 0 y 400 electrones primarios colectados
    histogramas[eng] = ROOT.TH1F(name, title, 80, 0, 400)
    
    print(f"\n>>> Simulando {eventos_por_energia} eventos para E = {eng} GeV...")
    for evento in range(eventos_por_energia):
        # Parámetro de impacto fijo a 3 mm del centro para consistencia
        # Graficamos únicamente el primer evento de cada ráfaga de energía
        graficar = (evento == 0)
        n_primarios = simular_evento(eng, 0.3, flag_graficar_evento=graficar)
        histogramas[eng].Fill(n_primarios)

# Guardar los objetos en un archivo ROOT estructurado para análisis posterior
f_out = ROOT.TFile("resolucion_energetica.root", "RECONSTRUCT")
for eng in energies:
    histogramas[eng].Write()
f_out.Close()
print("\n[Éxito] Datos crudos guardados en 'resolucion_energetica.root'")

# =========================================================================
# 7. RENDERIZACIÓN Y SUPERPOSICIÓN DE LA RESOLUCIÓN ENERGÉTICA
# =========================================================================
c_hist = ROOT.TCanvas("c_hist", "Resolucion Energetica Superpuesta", 900, 600)
ROOT.gStyle.SetOptStat(0)  # Limpiar la pantalla de cajas estadísticas redundantes

# Configurar la leyenda analítica
leyenda = ROOT.TLegend(0.65, 0.70, 0.88, 0.85)
leyenda.SetBorderSize(1)
leyenda.SetMargin(0.25)

# Paleta de colores para discriminar los histogramas
colores = [ROOT.kBlue - 4, ROOT.kRed - 4, ROOT.kGreen + 2]

for idx, eng in enumerate(energies):
    hist = histogramas[eng]
    hist.SetLineColor(colores[idx % len(colores)])
    hist.SetLineWidth(3)
    # Relleno semitransparente suave para mejorar el contraste visual
    hist.SetFillColorAlpha(colores[idx % len(colores)], 0.15)
    
    if idx == 0:
        hist.Draw("HIST")  # Dibuja el contorno estilo histograma limpio
    else:
        hist.Draw("HIST SAME")
        
    leyenda.AddEntry(hist, f"Muon: {eng} GeV", "lf")

leyenda.Draw()
c_hist.Update()
c_hist.SaveAs("espectro_resolucion_energetica.png")

print("\n[Listo] Gráficos generados. Presiona 'Enter' en la terminal para cerrar las ventanas...")
input()