// =========================================================================
// GEM 3D - Geometría y Mallado Adaptativo para Elmer FEM / Garfield++
// Archivo: gem.geo
// UNIDADES: milímetros [mm]
// =========================================================================

SetFactory("OpenCASCADE");

// -------------------------------------------------------------------------
// 1. Parámetros Geométricos [mm]
// -------------------------------------------------------------------------
pitch  = 0.140;   // Paso entre agujeros GEM
kapton = 0.050;   // Espesor del Kapton
metal  = 0.005;   // Espesor de cada capa de cobre
outdia = 0.070;   // Diámetro externo del agujero en el Kapton
middia = 0.050;   // Diámetro mínimo en el centro del Kapton
rimdia = 0.080;   // Diámetro del rim/clearance en el cobre

drift  = 1.000;   // Plano superior del volumen de gas (Drift)
induct = -1.000;  // Plano inferior del volumen de gas (Induction)

// Celda rectangular de simetría equivalente a la red hexagonal
Lx = pitch / 2;
Ly = Sqrt(3) * pitch / 2;

// Radios derivados
r_out = outdia / 2;
r_mid = middia / 2;
r_rim = rimdia / 2;

// -------------------------------------------------------------------------
// 2. Parámetros de Control de Malla [mm]
// -------------------------------------------------------------------------
lc_hole = 0.003;   // Elementos de 3 micras en el canal biconico y bordes
lc_gem  = 0.008;   // Elementos de 8 micras en la lámina GEM general
lc_gas  = 0.050;   // Elementos de 50 micras en zonas lejanas (gaps)

eps = 1.0e-6;

// -------------------------------------------------------------------------
// 3. Volúmenes Base
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
// 4. Herramientas Booleanas (Perforadores Bicónicos)
// -------------------------------------------------------------------------
// Agujero 1: Centro en (0, 0)
cut1_kap_bot = newv;
Cone(cut1_kap_bot) = {0, 0, -kapton/2, 0, 0, kapton/2, r_out, r_mid};

cut1_kap_top = newv;
Cone(cut1_kap_top) = {0, 0, 0, 0, 0, kapton/2, r_mid, r_out};

cut1_cu_bot = newv;
Cylinder(cut1_cu_bot) = {0, 0, -kapton/2 - metal, 0, 0, metal, r_rim};

cut1_cu_top = newv;
Cylinder(cut1_cu_top) = {0, 0, +kapton/2, 0, 0, metal, r_rim};

// Agujero 2: Centro en (Lx, Ly)
cut2_kap_bot = newv;
Cone(cut2_kap_bot) = {Lx, Ly, -kapton/2, 0, 0, kapton/2, r_out, r_mid};

cut2_kap_top = newv;
Cone(cut2_kap_top) = {Lx, Ly, 0, 0, 0, kapton/2, r_mid, r_out};

cut2_cu_bot = newv;
Cylinder(cut2_cu_bot) = {Lx, Ly, -kapton/2 - metal, 0, 0, metal, r_rim};

cut2_cu_top = newv;
Cylinder(cut2_cu_top) = {Lx, Ly, +kapton/2, 0, 0, metal, r_rim};

// -------------------------------------------------------------------------
// 5. Operaciones Booleanas de Perforación
// -------------------------------------------------------------------------
kapton_domain[] = BooleanDifference{ Volume{vol_kapton}; Delete; }{
  Volume{cut1_kap_bot, cut1_kap_top, cut2_kap_bot, cut2_kap_top}; Delete;
};

cu_bot_domain[] = BooleanDifference{ Volume{vol_cu_bot}; Delete; }{
  Volume{cut1_cu_bot, cut2_cu_bot}; Delete;
};

cu_top_domain[] = BooleanDifference{ Volume{vol_cu_top}; Delete; }{
  Volume{cut1_cu_top, cut2_cu_top}; Delete;
};

gas_domain[] = BooleanDifference{ Volume{vol_gas_box}; Delete; }{
  Volume{kapton_domain[], cu_bot_domain[], cu_top_domain[]};
};

Coherence;

// -------------------------------------------------------------------------
// 6. Grupos Físicos de Volumen (Identificadores para Elmer)
// -------------------------------------------------------------------------
Physical Volume("Gas_ArCO2_3bar", 1) = {gas_domain[]};
Physical Volume("Kapton",          2) = {kapton_domain[]};
Physical Volume("Copper_Bottom",   3) = {cu_bot_domain[]};
Physical Volume("Copper_Top",      4) = {cu_top_domain[]};

// -------------------------------------------------------------------------
// 7. Superficies Físicas para Condiciones de Frontera en Elmer
// -------------------------------------------------------------------------
s_drift[] = Surface In BoundingBox{-eps, -eps, drift - eps,
                                    Lx + eps, Ly + eps, drift + eps};

s_induct[] = Surface In BoundingBox{-eps, -eps, induct - eps,
                                     Lx + eps, Ly + eps, induct + eps};

s_cu_bot[] = Boundary{ Volume{cu_bot_domain[]}; };
s_cu_top[] = Boundary{ Volume{cu_top_domain[]}; };

Physical Surface("Drift_Plane",             11) = {s_drift[]};
Physical Surface("Induction_Plane",         12) = {s_induct[]};
Physical Surface("Copper_Bottom_Electrode", 13) = {s_cu_bot[]};
Physical Surface("Copper_Top_Electrode",    14) = {s_cu_top[]};

// -------------------------------------------------------------------------
// 8. Algoritmo de Refinamiento Adaptativo Basado en Campos
// -------------------------------------------------------------------------
// Campo 1: Calcula la distancia matemática exacta a los planos de cobre
Field[1] = Distance;
Field[1].SurfacesList = {s_cu_bot[], s_cu_top[]};
Field[1].Sampling = 150;

// Campo 2: Aplica un umbral. Si la distancia < 4 micras, fuerza tamaño lc_hole.
Field[2] = Threshold;
Field[2].InField = 1;
Field[2].SizeMin = lc_hole;
Field[2].SizeMax = lc_gas;
Field[2].DistMin = 0.004;
Field[2].DistMax = 0.100;

// Campo 3: Caja de contención fina alrededor de toda la oblea GEM
Field[3] = Box;
Field[3].VIn  = lc_gem;
Field[3].VOut = lc_gas;
Field[3].XMin = -eps;
Field[3].XMax = Lx + eps;
Field[3].YMin = -eps;
Field[3].YMax = Ly + eps;
Field[3].ZMin = -kapton/2 - metal - 0.030;
Field[3].ZMax = +kapton/2 + metal + 0.030;

// Campo 4: Elige el elemento más pequeño entre el umbral local y la caja GEM
Field[4] = Min;
Field[4].FieldsList = {2, 3};
Background Field = 4;

// -------------------------------------------------------------------------
// 9. Configuración de Compatibilidad y Exportación MSH v2.2
// -------------------------------------------------------------------------
Mesh.MshFileVersion = 2.2; // Formato requerido estrictamente por ElmerGrid
Mesh.SaveAll = 0;          // Solo exportar entidades dentro de Physical Groups

Mesh.Algorithm = 6;        // Frontal-Delaunay 2D
Mesh.Algorithm3D = 1;      // Delaunay 3D nativo uniforme
Mesh.Optimize = 1;
Mesh.OptimizeNetgen = 0;   // Evita dependencias externas de Netgen
Mesh.ElementOrder = 2;     

Mesh.MeshSizeMin = lc_hole;
Mesh.MeshSizeMax = lc_gas;
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 20;
Mesh.MeshSizeExtendFromBoundary = 1;
Show;