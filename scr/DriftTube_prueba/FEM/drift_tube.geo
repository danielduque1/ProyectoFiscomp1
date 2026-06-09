// =========================================================================
// GEOMETRÍA CILÍNDRICA PARA TUBO DE DERIVA (MDT) - FORMATO .GEO
// =========================================================================

// Parámetros físicos en centímetros (cm)
R_a = 0.002;  // Radio del alambre (Ánodo): 20 um
R_b = 1.0;    // Radio del tubo exterior (Cátodo): 1 cm

// Tamaños característicos de los elementos de malla (lc)
lc_anodo  = 0.0002;  // Densidad alta cerca al alambre (2 um)
lc_catodo = 0.01;    // Densidad estándar en la frontera externa (100 um)

// 1. Crear Puntos Geométricos (Centro, Ánodo y Cátodo)
c  = newp; Point(c)  = {0, 0, 0, 0};
p1 = newp; Point(p1) = {R_a, 0, 0, lc_anodo};
p2 = newp; Point(p2) = {0, R_a, 0, lc_anodo};
p3 = newp; Point(p3) = {-R_a, 0, 0, lc_anodo};
p4 = newp; Point(p4) = {0, -R_a, 0, lc_anodo};

p5 = newp; Point(p5) = {R_b, 0, 0, lc_catodo};
p6 = newp; Point(p6) = {0, R_b, 0, lc_catodo};
p7 = newp; Point(p7) = {-R_b, 0, 0, lc_catodo};
p8 = newp; Point(p8) = {0, -R_b, 0, lc_catodo};

// 2. Crear los Arcos Circulares (Fronteras 1D)
// Ánodo (Interno)
a1 = newc; Circle(a1) = {p1, c, p2};
a2 = newc; Circle(a2) = {p2, c, p3};
a3 = newc; Circle(a3) = {p3, c, p4};
a4 = newc; Circle(a4) = {p4, c, p1};

// Cátodo (Externo)
a5 = newc; Circle(a5) = {p5, c, p6};
a6 = newc; Circle(a6) = {p6, c, p7};
a7 = newc; Circle(a7) = {p7, c, p8};
a8 = newc; Circle(a8) = {p8, c, p5};

// 3. Definir Contornos (Loops) y Superficies (2D)
ll_anodo  = newreg; Line Loop(ll_anodo)  = {a1, a2, a3, a4};
ll_catodo = newreg; Line Loop(ll_catodo) = {a5, a6, a7, a8};

// Superficie 1: Espacio del Gas (El anillo entre el cátodo y el ánodo)
ps_gas = newreg; Plane Surface(ps_gas) = {ll_catodo, ll_anodo};

// Superficie 2: El cuerpo conductor del Alambre (El círculo interno completo)
ps_wire = newreg; Plane Surface(ps_wire) = {ll_anodo};

// 4. Definir Grupos Físicos (Crucial para el mapeo de Elmer)
phys_catodo = newreg; Physical Curve(phys_catodo) = {a5, a6, a7, a8}; // Frontera Cátodo (ID: 1)
phys_anodo  = newreg; Physical Curve(phys_anodo)  = {a1, a2, a3, a4}; // Frontera Ánodo  (ID: 2)

phys_s_gas  = newreg; Physical Surface(phys_s_gas)   = {ps_gas};      // Volumen Gas     (ID: 3)
phys_s_wire = newreg; Physical Surface(phys_s_wire)  = {ps_wire};     // Volumen Alambre (ID: 4)

// 5. Banderas del Algoritmo Serendipity (Forzar Cuadriláteros de 8 Nodos)
Mesh.RecombinationAlgorithm = 2;
Mesh.ElementOrder = 2;
Mesh.SecondOrderIncomplete = 1; // Elimina el nodo central -> Bloques de 8 nodos estrictos
Mesh.SubdivisionAlgorithm = 1;  # Subdivisión total a cuadriláteros

// Comandos imperativos secuenciales de generación
Mesh 2;
RecombineMesh;
RefineMesh;