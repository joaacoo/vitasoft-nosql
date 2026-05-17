from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from src.etl.etl_mongo import extract_data, transform_data, load_to_mongodb
from src.sync.sync_neo4j import get_latest_data_from_mongo, sync_to_neo4j, NEO4J_URI, NEO4J_USER, NEO4J_PASS
from neo4j import GraphDatabase

app = FastAPI()

# Para permitir que el frontend (HTML simple) haga requests a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detectar_fraudes_neo4j():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    alertas = []
    
    query = """
    MATCH (p1:Proveedor)-[:TIENE_CBU]->(c:CBU)<-[:TIENE_CBU]-(p2:Proveedor)
    WHERE id(p1) < id(p2)
    RETURN p1.nombre AS prov1, p2.nombre AS prov2, c.numero AS cbu
    """
    
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            alertas.append({
                "prov1": record["prov1"],
                "prov2": record["prov2"],
                "cbu": record["cbu"]
            })
    driver.close()
    return alertas

from src.etl.exportador_txt import generar_txt_bancario

@app.post("/api/procesar")
async def procesar_lote(file: UploadFile = File(...)):
    # Guardar el archivo temporalmente
    temp_path = f"data/temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 1. ETL a MongoDB
    datos = extract_data(temp_path)
    if datos is None:
        return {"error": "No se pudo leer el archivo. Asegúrate de que sea CSV o XLSX."}
        
    datos_limpios = transform_data(datos)
    total_monto = datos_limpios['monto'].sum()
    cantidad_registros = len(datos_limpios)
    
    id_lote = load_to_mongodb(datos_limpios)
    
    # 1.5 Exportar a TXT
    ruta_txt = generar_txt_bancario(id_lote)
    
    # 2. Sync a Neo4j
    datos_mongo = get_latest_data_from_mongo()
    sync_to_neo4j(datos_mongo)
    
    # 3. Consultar fraudes en Neo4j
    alertas = detectar_fraudes_neo4j()
    
    # Limpiar archivo temporal
    os.remove(temp_path)
    
    return {
        "status": "success",
        "registros": cantidad_registros,
        "total_monto": float(total_monto),
        "archivo_txt": ruta_txt,
        "alertas": alertas
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
