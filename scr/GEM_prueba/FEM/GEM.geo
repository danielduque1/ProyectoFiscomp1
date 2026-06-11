// =========================================================================
// GEOMETRÍA 3D GEM - CORRECCIÓN DE BOOLEANAS Y MALLADO (OpenCASCADE)
// =========================================================================

SetFactory("OpenCASCADE");

// --- 1. PARÁMETROS GEOMÉTRICOS (mm) ---
pitch  = 0.140;       // Distancia entre agujeros [cite: 27]
kapton = 0.050;       // Espesor de la capa de Kapton [cite: 28]
metal  = 0.005;       // Espesor de las capas de metal [cite: 29]
outdia = 0.070;       // Diámetro exterior del agujero [cite: 30]
middia = 0.050;       // Diámetro en el centro [cite: 31]
drift  = 1.000;       // Región de deriva [cite: 32]
induct = 1.000;       // Espacio de inducción [cite: 33]

// Dimensiones de la celda
X_max = pitch;
Y_max = pitch * Sqrt(3) / 2.0;
x_min = -X_max / 2.0; x_max = X_max / 2.0;
y_min = -Y_max / 2.0; y_max = Y_max / 2.0;

// Resoluciones de malla
lc_inf  = 0.035;
lc_hole = 0.003;

// --- 2. CAJAS PRIMITIVAS (Capas Sólidas Totales) ---
v_mt_raw = newv; Box(v_mt_raw) = {x_min, y_min, kapton/2, X_max, Y_max, metal};
v_k_raw  = newv; Box(v_k_raw)  = {x_min, y_min, -kapton/2, X_max, Y_max, kapton};
v_mb_raw = newv; Box(v_mb_raw) = {x_min, y_min, -kapton/2 - metal, X_max, Y_max, metal};

v_drift = newv; Box(v_drift) = {x_min, y_min, kapton/2 + metal, X_max, Y_max, drift};
v_induct= newv; Box(v_induct)= {x_min, y_min, -kapton/2 - metal - induct, X_max, Y_max, induct};

// --- 3. CONSTRUCCIÓN DEL "PIN" DE PERFORACIÓN (Cilindro + Bicono + Cilindro) ---
Macro HoleMacro
    // Cilindro Metal Inferior 
    cyl_b = newv; Cylinder(cyl_b) = {cx, cy, -kapton/2 - metal, 0, 0, metal, outdia/2, 2*Pi};
    // Cono Kapton Inferior 
    con_b = newv; Cone(con_b)     = {cx, cy, -kapton/2, 0, 0, kapton/2, outdia/2, middia/2, 2*Pi};
    // Cono Kapton Superior 
    con_t = newv; Cone(con_t)     = {cx, cy, 0, 0, 0, kapton/2, middia/2, outdia/2, 2*Pi};
    // Cilindro Metal Superior 
    cyl_t = newv; Cylinder(cyl_t) = {cx, cy, kapton/2, 0, 0, metal, outdia/2, 2*Pi};

    // Fusionar todo en una sola herramienta sólida
    f1[]  = BooleanUnion{ Volume{cyl_b}; Delete; }{ Volume{con_b}; Delete; };
    f2[]  = BooleanUnion{ Volume{f1[0]}; Delete; }{ Volume{con_t}; Delete; };
    pin[] = BooleanUnion{ Volume{f2[0]}; Delete; }{ Volume{cyl_t}; Delete; };
    all_pins[] += {pin[0]};
Return

all_pins[] = {};
cx = 0;     cy = 0;     Call HoleMacro;
cx = x_min; cy = y_min; Call HoleMacro;
cx = x_max; cy = y_min; Call HoleMacro;
cx = x_min; cy = y_max; Call HoleMacro;
cx = x_max; cy = y_max; Call HoleMacro;

// Unir los 5 pines y recortar excesos fuera de la celda unitaria
tool_raw[] = BooleanUnion{ Volume{all_pins[0]}; Delete; }{ Volume{all_pins[1], all_pins[2], all_pins[3], all_pins[4]}; Delete; };
v_bound = newv; Box(v_bound) = {x_min, y_min, -2, X_max, Y_max, 4};
gas_holes[] = BooleanIntersection{ Volume{tool_raw[0]}; Delete; }{ Volume{v_bound}; Delete; };

// --- 4. EXTRACCIÓN BOOLEANA (Rompecabezas Exacto) ---
// Sustraemos la herramienta de las capas sólidas para crear las perforaciones
v_mt[] = BooleanSubtraction{ Volume{v_mt_raw}; Delete; }{ Volume{gas_holes[0]}; }; 
v_k[]  = BooleanSubtraction{ Volume{v_k_raw};  Delete; }{ Volume{gas_holes[0]}; };
v_mb[] = BooleanSubtraction{ Volume{v_mb_raw}; Delete; }{ Volume{gas_holes[0]}; };

// Unimos el volumen de los agujeros con las zonas de deriva e inducción
gas_total[] = BooleanUnion{ Volume{v_drift}; Volume{v_induct}; Delete; }{ Volume{gas_holes[0]}; Delete; };

// --- 5. ASIGNACIÓN FÍSICA ---
// Se asignan los volúmenes ANTES de la coherencia para preservar los identificadores exactos
Physical Volume("Gas") = {gas_total[0]};
Physical Volume("Kapton") = {v_k[0]};
Physical Volume("Metal_Superior") = {v_mt[0]};
Physical Volume("Metal_Inferior") = {v_mb[0]};

eps = 0.001;
surf_drift[]     = Surface In BoundingBox {x_min-eps, y_min-eps, drift+kapton/2+metal-eps, x_max+eps, y_max+eps, drift+kapton/2+metal+eps};
surf_induction[] = Surface In BoundingBox {x_min-eps, y_min-eps, -induct-kapton/2-metal-eps, x_max+eps, y_max+eps, -induct-kapton/2-metal+eps};

Physical Surface("Plano_Drift")     = {surf_drift[]};
Physical Surface("Plano_Induction") = {surf_induction[]};

// --- 6. COHERENCIA DE FRONTERAS (Equivalente al VGLUE de ANSYS) ---
Coherence;

// --- 7. CONTROL DE MALLADO ---
Mesh.CharacteristicLengthMin = lc_hole;
Mesh.CharacteristicLengthMax = lc_inf;

// Forzar una densidad nodal alta dentro y alrededor del canal de avalancha
Field[1] = Cylinder;
Field[1].Radius = outdia * 1.5;
Field[1].VIn = lc_hole;
Field[1].VOut = lc_inf;
Field[1].XAxis = 0; Field[1].YAxis = 0; Field[1].ZAxis = 1;
Field[1].XCenter = 0; Field[1].YCenter = 0; Field[1].ZCenter = 0;
Background Field = 1;

// Ajustes obligatorios para que Elmer resuelva el gradiente de 50 kV/cm
Mesh.ElementOrder = 2;
Mesh.SecondOrderIncomplete = 1;

Mesh 3;

Show;