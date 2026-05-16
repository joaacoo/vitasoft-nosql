// 1. Detectar Fraude Básico: Dos proveedores distintos comparten el mismo CBU
// Explicación: Riesgo crítico de desvío de fondos. CUITs diferentes cobrando en la misma cuenta.
MATCH (p1:Proveedor)-[:TIENE_CBU]->(c:CBU)<-[:TIENE_CBU]-(p2:Proveedor)
WHERE p1.cuit < p2.cuit
RETURN p1.nombre, p2.nombre, c.numero AS CBU_Compartido;

// 2. Detectar Fraude Básico: Dos proveedores comparten la misma Dirección física
// Explicación: Posibles empresas fantasma o desdoblamiento fiscal.
MATCH (p1:Proveedor)-[:DOMICILIADO_EN]->(d:Direccion)<-[:DOMICILIADO_EN]-(p2:Proveedor)
WHERE p1.cuit < p2.cuit
RETURN p1.nombre, p2.nombre, d.calle AS Direccion_Compartida;

// 3. Relaciones Indirectas (Redes Sospechosas / Grupos Económicos No Declarados)
// Explicación: El Proveedor A comparte CBU con B, y B comparte Dirección con C.
// Permite detectar clusters de fraude imposibles de ver con simples JOINs SQL.
MATCH path = (p1:Proveedor)-[:TIENE_CBU|DOMICILIADO_EN*2..4]-(p2:Proveedor)
WHERE p1 <> p2
RETURN path LIMIT 10;

// 4. Análisis de Concentración: Cuentas que reciben transferencias de más de 2 empresas
MATCH (c:CBU)<-[:TIENE_CBU]-(p:Proveedor)
WITH c, count(p) as cant_proveedores, collect(p.nombre) as empresas
WHERE cant_proveedores >= 2
RETURN c.numero, cant_proveedores, empresas
ORDER BY cant_proveedores DESC;
