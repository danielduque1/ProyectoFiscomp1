import Garfield

# 1. Inicializar Magboltz
gas = Garfield.MediumMagboltz()
gas.SetComposition('Ar', 80.0, 'CO2', 20.0)
gas.SetTemperature(293.15)
gas.SetPressure(760.0)

# 2. Configurar el barrido de Campos Eléctricos (E-fields)
# Debemos simular desde campos bajos (zona de deriva) hasta campos ultra altos (zona de avalancha)
# Definimos el número de puntos de muestreo
n_campos = 50
e_min = 100.0     # 100 V/cm
e_max = 100000.0  # 100 kV/cm (crucial para la avalancha cerca del hilo)

# Establecer el barrido en escala logarítmica (más denso en campos bajos y medios)
gas.SetFieldGrid(e_min, e_max, n_campos, True)

# 3. Configurar los parámetros de simulación de Monte Carlo de Magboltz
# Número de colisiones a simular por cada punto de campo eléctrico (en múltiplos de 10^7)
# Un valor de 2 a 5 da buena precisión estadística sin tardar días.
n_colisiones = 2
gas.SetMaxElectronEnergy(200.0) # Energía máxima en eV que se le permite alcanzar a un electrón

# 4. Ejecutar el cálculo de Magboltz
print(f"Iniciando el cálculo de Magboltz para {n_campos} puntos de campo eléctrico...")
print("Esto puede tomar desde unos minutos hasta un par de horas dependiendo de tu CPU...")

# Corre la simulación de colisiones microscópicas para llenar la tabla
gas.GenerateGasTable(n_colisiones)

# 5. Guardar el archivo en el disco
nombre_archivo = "ar_80_co2_20_generado.gas"
gas.WriteGasFile("data/outputs/" + nombre_archivo)
print(f"¡Proceso completado con éxito! Archivo guardado como: {nombre_archivo}")