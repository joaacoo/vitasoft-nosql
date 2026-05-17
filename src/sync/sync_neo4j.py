from pymongo import MongoClient
from neo4j import GraphDatabase

# Configuraciones
MONGO_URI = "mongodb://localhost:27017/"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "vitasoft2026"

def get_latest_data_from_mongo():
    client = MongoClient(MONGO_URI)
    db = client["vitasoft_db"]
    # Traemos los proveedores para sincronizar
    proveedores_cursor = db.proveedores.find({})
    proveedores = []
    for p in proveedores_cursor:
        # Convertimos _id a string y fecha a string para que neo4j no falle
        p['_id'] = str(p['_id'])
        if 'fecha_actualizacion' in p:
            p['fecha_actualizacion'] = str(p['fecha_actualizacion'])
        proveedores.append(p)
    client.close()
    return proveedores

def sync_to_neo4j(proveedores):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    
    query = """
    UNWIND $proveedores AS prov
    
    // Crear/Actualizar Nodos
    MERGE (p:Proveedor {cuit: prov.cuit})
    SET p.nombre = prov.nombre
    
    MERGE (c:CBU {numero: prov.ultimo_cbu})
    MERGE (d:Direccion {calle: prov.ultima_direccion})
    
    // Crear Relaciones
    MERGE (p)-[:TIENE_CBU]->(c)
    MERGE (p)-[:DOMICILIADO_EN]->(d)
    """
    
    with driver.session() as session:
        session.run(query, proveedores=proveedores)
        print(f"Sincronizados {len(proveedores)} nodos/relaciones en Neo4j.")
    
    driver.close()

if __name__ == "__main__":
    datos = get_latest_data_from_mongo()
    sync_to_neo4j(datos)
