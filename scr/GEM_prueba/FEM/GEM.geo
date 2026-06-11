// =========================================================================
// GEM 3D - Geometria lista para Gmsh -> Elmer FEM -> Garfield++
// =========================================================================
// Basado en:
//   (1) drift_tube.geo: estructura por parametros y Physical Groups.
//   (2) Ejemplo GEM Garfield/ANSYS: celda rectangular de simetria,
//       Kapton + cobres + gas + agujeros biconicos en esquinas opuestas.
//
// UNIDADES: milimetros [mm]
//
// Convencion en z:
//   z = 0                                  centro del Kapton
//   -kapton/2 <= z <= +kapton/2            Kapton
//   -kapton/2-metal <= z <= -kapton/2      cobre inferior
//   +kapton/2 <= z <= +kapton/2+metal      cobre superior
//   induct <= z <= drift                   volumen total de gas
//
// Identificacion para Elmer:
//   Physical Volume 1  : Gas_ArCO2_3bar
//   Physical Volume 2  : Kapton
//   Physical Volume 3  : Copper_Bottom
//   Physical Volume 4  : Copper_Top
//
//   Physical Surface 11: Drift_Plane
//   Physical Surface 12: Induction_Plane
//   Physical Surface 13: Copper_Bottom_Electrode
//   Physical Surface 14: Copper_Top_Electrode
//
// Nota importante:
//   Los conos/cilindros usados para cortar los agujeros se eliminan con Delete.
//   Por eso la geometria final NO contiene cuerpos auxiliares; solo quedan gas,
//   Kapton y cobres, lista para mallar y convertir con ElmerGrid.
// =========================================================================

SetFactory("OpenCASCADE");

// -------------------------------------------------------------------------
// 1. Parametros geometricos [mm]
// -------------------------------------------------------------------------
pitch  = 0.140;   // paso entre agujeros GEM [mm]
kapton = 0.050;   // espesor del Kapton [mm]
metal  = 0.005;   // espesor de cada capa de cobre [mm]
outdia = 0.070;   // diametro externo del agujero en Kapton [mm]
middia = 0.050;   // diametro minimo en el centro del Kapton [mm]
rimdia = 0.080;   // diametro del rim/clearance en el cobre [mm]

drift  = 1.000;   // plano superior del gas [mm]
induct = -1.000;  // plano inferior del gas [mm]

// Celda rectangular de simetria equivalente a la red hexagonal.
// Es la misma idea del codigo Garfield/ANSYS.
Lx = pitch/2;
Ly = Sqrt(3)*pitch/2;

// Radios derivados
r_out = outdia/2;
r_mid = middia/2;
r_rim = rimdia/2;

// -------------------------------------------------------------------------
// 2. Parametros de malla [mm]
// -------------------------------------------------------------------------
// Recuerda: 0.003 mm = 3 micras.
lc_hole = 0.003;   // muy fino cerca del agujero y del cobre
lc_gem  = 0.008;   // fino alrededor de Kapton/cobre
lc_gas  = 0.050;   // mas grueso lejos de la lamina GEM

eps = 1.0e-6;

// -------------------------------------------------------------------------
// 3. Volumenes base
// -------------------------------------------------------------------------
vol_kapton = newv;
Box(vol_kapton) = {0, 0, -kapton/2, Lx, Ly, kapton};

vol_cu_bot = newv;
Box(vol_cu_bot) = {0, 0, -kapton/2 - metal, Lx, Ly, metal};

vol_cu_top = newv;
Box(vol_cu_top) = {0, 0, +kapton/2, Lx, Ly, metal};

vol_gas_box = newv;
Box(vol_gas_box) = {0, 0, induct, Lx, Ly, drift - induct};

// -------------------------------------------------------------------------
// 4. Herramientas booleanas para perforar los agujeros
// -------------------------------------------------------------------------
// El ejemplo ANSYS coloca los agujeros en dos esquinas opuestas de la celda:
//   agujero 1: (0, 0)
//   agujero 2: (Lx, Ly)
// Dentro del dominio queda la fraccion correspondiente del agujero, lo cual
// es compatible con una celda de simetria/periodica.

// ---------------- Agujero 1: centro en (0, 0) ----------------
cut1_kap_bot = newv;
Cone(cut1_kap_bot) = {0, 0, -kapton/2, 0, 0, kapton/2, r_out, r_mid};

cut1_kap_top = newv;
Cone(cut1_kap_top) = {0, 0, 0, 0, 0, kapton/2, r_mid, r_out};

cut1_cu_bot = newv;
Cylinder(cut1_cu_bot) = {0, 0, -kapton/2 - metal, 0, 0, metal, r_rim};

cut1_cu_top = newv;
Cylinder(cut1_cu_top) = {0, 0, +kapton/2, 0, 0, metal, r_rim};

// ---------------- Agujero 2: centro en (Lx, Ly) ----------------
cut2_kap_bot = newv;
Cone(cut2_kap_bot) = {Lx, Ly, -kapton/2, 0, 0, kapton/2, r_out, r_mid};

cut2_kap_top = newv;
Cone(cut2_kap_top) = {Lx, Ly, 0, 0, 0, kapton/2, r_mid, r_out};

cut2_cu_bot = newv;
Cylinder(cut2_cu_bot) = {Lx, Ly, -kapton/2 - metal, 0, 0, metal, r_rim};

cut2_cu_top = newv;
Cylinder(cut2_cu_top) = {Lx, Ly, +kapton/2, 0, 0, metal, r_rim};

// -------------------------------------------------------------------------
// 5. Perforar Kapton y cobres
// -------------------------------------------------------------------------
// Kapton: agujero biconico, radio grande en las caras y pequeno en z = 0.
kapton_domain[] = BooleanDifference{ Volume{vol_kapton}; Delete; }{
  Volume{cut1_kap_bot, cut1_kap_top, cut2_kap_bot, cut2_kap_top}; Delete;
};

// Cobre inferior y superior: clearance/rim cilindrico.
cu_bot_domain[] = BooleanDifference{ Volume{vol_cu_bot}; Delete; }{
  Volume{cut1_cu_bot, cut2_cu_bot}; Delete;
};

cu_top_domain[] = BooleanDifference{ Volume{vol_cu_top}; Delete; }{
  Volume{cut1_cu_top, cut2_cu_top}; Delete;
};

// -------------------------------------------------------------------------
// 6. Gas final
// -------------------------------------------------------------------------
// El gas ocupa el drift gap, el induction gap y el interior de los agujeros.
// Para lograrlo, al bloque de gas total se le restan los solidos ya perforados.
// OJO: aqui NO se usa Delete sobre Kapton/cobres, para conservarlos como
// volumenes fisicos independientes.
gas_domain[] = BooleanDifference{ Volume{vol_gas_box}; Delete; }{
  Volume{kapton_domain[], cu_bot_domain[], cu_top_domain[]};
};

Coherence;

// -------------------------------------------------------------------------
// 7. Grupos fisicos de volumen para Elmer
// -------------------------------------------------------------------------
Physical Volume("Gas_ArCO2_3bar", 1) = {gas_domain[]};
Physical Volume("Kapton",          2) = {kapton_domain[]};
Physical Volume("Copper_Bottom",   3) = {cu_bot_domain[]};
Physical Volume("Copper_Top",      4) = {cu_top_domain[]};

// -------------------------------------------------------------------------
// 8. Superficies fisicas para condiciones de frontera en Elmer
// -------------------------------------------------------------------------
// Planos externos del gas.
s_drift[] = Surface In BoundingBox{-eps, -eps, drift - eps,
                                   Lx + eps, Ly + eps, drift + eps};

s_induct[] = Surface In BoundingBox{-eps, -eps, induct - eps,
                                    Lx + eps, Ly + eps, induct + eps};

// Electrodos: toda la frontera de cada volumen de cobre.
// Esto reproduce la idea del ejemplo ANSYS: seleccionar el volumen metalico,
// tomar sus areas asociadas y aplicar VOLT sobre ellas.
s_cu_bot[] = Boundary{ Volume{cu_bot_domain[]}; };
s_cu_top[] = Boundary{ Volume{cu_top_domain[]}; };

Physical Surface("Drift_Plane",             11) = {s_drift[]};
Physical Surface("Induction_Plane",         12) = {s_induct[]};
Physical Surface("Copper_Bottom_Electrode", 13) = {s_cu_bot[]};
Physical Surface("Copper_Top_Electrode",    14) = {s_cu_top[]};

// Nota sobre las fronteras laterales:
// En Elmer, si no asignas una condicion de frontera en las caras laterales,
// queda la condicion natural de flujo normal nulo, equivalente a simetria
// electrostatica. Por eso no se crean Physical Surfaces laterales aqui, para
// evitar que una misma cara pertenezca a la vez a simetria y a electrodo.

// -------------------------------------------------------------------------
// 9. Refinamiento de malla
// -------------------------------------------------------------------------
// Campo 1: distancia a superficies de cobre. Refina cerca de electrodos y rim.
Field[1] = Distance;
Field[1].SurfacesList = {s_cu_bot[], s_cu_top[]};
Field[1].Sampling = 150;

// Campo 2: umbral de refinamiento alrededor del GEM.
Field[2] = Threshold;
Field[2].InField = 1;
Field[2].SizeMin = lc_hole;
Field[2].SizeMax = lc_gas;
Field[2].DistMin = 0.004;
Field[2].DistMax = 0.100;

// Campo 3: caja fina alrededor de toda la lamina GEM.
Field[3] = Box;
Field[3].VIn  = lc_gem;
Field[3].VOut = lc_gas;
Field[3].XMin = -eps;
Field[3].XMax = Lx + eps;
Field[3].YMin = -eps;
Field[3].YMax = Ly + eps;
Field[3].ZMin = -kapton/2 - metal - 0.030;
Field[3].ZMax = +kapton/2 + metal + 0.030;

// Malla final: toma el minimo entre refinamiento local y caja del GEM.
Field[4] = Min;
Field[4].FieldsList = {2, 3};
Background Field = 4;

// -------------------------------------------------------------------------
// 10. Opciones de mallado compatibles con ElmerGrid
// -------------------------------------------------------------------------
Mesh.MshFileVersion = 2.2;
Mesh.SaveAll = 0;

Mesh.Algorithm = 6;        // Frontal-Delaunay 2D
Mesh.Algorithm3D = 1;      // Delaunay 3D: no requiere Netgen
Mesh.Optimize = 1;
Mesh.OptimizeNetgen = 0;   // Desactivado: tu Gmsh no tiene Netgen
Mesh.ElementOrder = 1;     // iniciar con tetraedros lineales para Elmer

Mesh.MeshSizeMin = lc_hole;
Mesh.MeshSizeMax = lc_gas;
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 20;
Mesh.MeshSizeExtendFromBoundary = 1;

// Para inspeccionar primero la geometria, deja esta linea comentada.
// Para generar desde la interfaz grafica: Modules -> Mesh -> 3D.
// Para terminal: gmsh -3 gem_elmer_ready.geo -format msh2 -o gem.msh
// Mesh 3;

Show;