import ROOT
# Forzamos a ROOT a cargar la librería dinámica de Garfield en memoria
ROOT.gSystem.Load("libGarfield") 

# Invocamos la clase desde el espacio de nombres de ROOT o el entorno global de C++
gas = ROOT.Garfield.MediumMagboltz()

print("¡Conexión exitosa! Objeto creado:", gas)