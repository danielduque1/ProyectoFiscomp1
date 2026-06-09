from pathlib import Path

import gmsh


ubicacion_script = Path(__file__).resolve().parent

gmsh.initialize()
gmsh.model.add("drift_tube")

### Parametros en cm

R_a = 0.002 # Radio del alambre (ánodo): 20 um
R_b = 1.0   # Radio del tubo (cátodo): 1 cm

# Tamaños del elemento de malla

lc_anodo = 0.0002  # 2um
lc_catodo = 0.01   # 100 um

### Crear puntos geometricos (Centro, Ánodo, Cátado)

# gmsh.model.geo.addPoint(x, y, z, lc) -> devuelve el ID del punto creado con tamaño de malla lc
# un punto tiene dim 0

c = gmsh.model.geo.addPoint(0, 0, 0, 0)
p1 = gmsh.model.geo.addPoint(R_a, 0, 0, lc_anodo)
p2 = gmsh.model.geo.addPoint(0, R_a, 0, lc_anodo)
p3 = gmsh.model.geo.addPoint(-R_a, 0, 0, lc_anodo)
p4 = gmsh.model.geo.addPoint(0, -R_a, 0, lc_anodo)

p5 = gmsh.model.geo.addPoint(R_b, 0, 0, lc_catodo)
p6 = gmsh.model.geo.addPoint(0, R_b, 0, lc_catodo)
p7 = gmsh.model.geo.addPoint(-R_b, 0, 0, lc_catodo)
p8 = gmsh.model.geo.addPoint(0, -R_b, 0, lc_catodo)

### Crear los arcos para el ánodo y el cátodo

# gmsh.model.geo.addCircleArc(p1, c, p2) -> devuelve el ID del arco creado entre p1 y p2 con centro en c
# un arco o segmento tiene dim 1

# Ánodo  (interno)
a1 = gmsh.model.geo.addCircleArc(p1, c, p2)
a2 = gmsh.model.geo.addCircleArc(p2, c, p3)
a3 = gmsh.model.geo.addCircleArc(p3, c, p4)
a4 = gmsh.model.geo.addCircleArc(p4, c, p1)

# Cátodo (externo)

a5 = gmsh.model.geo.addCircleArc(p5, c, p6)
a6 = gmsh.model.geo.addCircleArc(p6, c, p7)
a7 = gmsh.model.geo.addCircleArc(p7, c, p8)
a8 = gmsh.model.geo.addCircleArc(p8, c, p5)

### Definir contornos (Loops) y Superficies del Gas

# gmsh.model.geo.addCurveLoop([a1, a2, a3, a4]) -> devuelve el ID del loop creado con los arcos dados
# un loop es una frontera no una entidad geometrica, pero es necesario para 
# definir la superficie del gas entre el ánodo y el cátodo

loop_anodo = gmsh.model.geo.addCurveLoop([a1, a2, a3, a4])
loop_catodo = gmsh.model.geo.addCurveLoop([a5, a6, a7, a8])

# gmsh.model.geo.addPlaneSurface([loop_catodo, loop_anodo]) -> devuelve el ID de la superficie creada entre los loops dados
# una superficie tiene dim 2

gas_surface = gmsh.model.geo.addPlaneSurface([loop_catodo, loop_anodo])

gmsh.model.geo.synchronize() # --> paso necesario.

### Definir grupos físicos

# gmsh.model.addPhysicalGroup(dim, [IDs], name="Nombre") -> devuelve el ID del grupo físico creado con las entidades dadas
# este ID es el que luego se usa en el script .sif de Elmer
# se asigna en el orden que se escribe

gmsh.model.addPhysicalGroup(1, [a1, a2, a3, a4], name="Anodo")      # ID: 1
gmsh.model.addPhysicalGroup(1, [a5, a6, a7, a8], name="Catodo")     # ID: 2
gmsh.model.addPhysicalGroup(2, [gas_surface], name="Gas")           # ID: 3

### Generar la malla

gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 2)
gmsh.option.setNumber("Mesh.ElementOrder", 2)            # Segundo orden activo
gmsh.option.setNumber("Mesh.SecondOrderIncomplete", 1)   # Forzar 8 nodos (Serendipity)
gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 1)    # Subdividir todo a cuadriláteros

gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)

# Generar la malla 2D estructurada
gmsh.model.mesh.generate(2)

# Aplicar la recombinación explícita sobre el modelo físico
gmsh.model.mesh.recombine()
# =========================================================================

# Guardar la malla
gmsh.write(str(ubicacion_script / "drift_tube.msh"))
print("Malla cuadrangular 2D de 8 nodos generada y guardada con éxito.")

gmsh.fltk.run() # Grafica la malla para inspección visual
gmsh.finalize()