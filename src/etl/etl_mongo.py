import pandas as pd
from pymongo import MongoClient
import datetime
import uuid

# Configuración MongoDB
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "vitasoft_db"

def extract_data(filepath):
    print(f"Leyendo archivo {filepath}...")
    try:
        # Asegurar que cuit y cbu se lean siempre como texto para no perder ceros a la izquierda
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, comment='#', dtype={'cuit': str, 'cbu': str})
        else:
            df = pd.read_excel(filepath, engine='openpyxl', dtype={'cuit': str, 'cbu': str})
        return df
    except Exception as e:
        print(f"Error crítico al leer el archivo: {e}")
        return None

def transform_data(df):
    # Limpiamos y normalizamos los datos
    df['proveedor'] = df['proveedor'].str.strip().str.upper()
    df['cuit'] = df['cuit'].astype(str).str.strip()
    df['cbu'] = df['cbu'].astype(str).str.strip()
    df['banco'] = df['banco'].str.strip().str.upper()
    df['direccion'] = df['direccion'].str.strip().str.upper()
    df['monto'] = pd.to_numeric(df['monto'], errors='coerce')
    
    # Eliminar nulos críticos
    df = df.dropna(subset=['cuit', 'cbu', 'monto'])
    return df

def load_to_mongodb(df):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    id_lote = str(uuid.uuid4())
    fecha_proceso = datetime.datetime.now()
    
    lote_doc = {
        "id_lote": id_lote,
        "fecha_proceso": fecha_proceso,
        "cantidad_registros": len(df),
        "estado": "PROCESADO",
        "pagos": [],
        "historial": [
            {
                "fecha": fecha_proceso,
                "accion": "procesamiento",
                "detalle": "Lote ingerido y procesado desde archivo fuente"
            }
        ]
    }
    
    for _, row in df.iterrows():
        pago = {
            "proveedor": row['proveedor'],
            "cuit": row['cuit'],
            "cbu": row['cbu'],
            "banco": row['banco'],
            "direccion": row['direccion'],
            "monto": row['monto'],
            "concepto": row['concepto']
        }
        lote_doc["pagos"].append(pago)

        # Upsert en colección de proveedores para mantener padrón actualizado y que Neo4j funcione después
        db.proveedores.update_one(
            {"cuit": row['cuit']},
            {"$set": {
                "nombre": row['proveedor'],
                "ultima_direccion": row['direccion'],
                "ultimo_cbu": row['cbu'],
                "ultimo_banco": row['banco'],
                "fecha_actualizacion": fecha_proceso
            }},
            upsert=True
        )

    # Insertamos todo el lote transaccional
    db.lotes_pago.insert_one(lote_doc)
    print(f"¡Éxito! Lote {id_lote} cargado en MongoDB con {len(df)} registros.")
    client.close()
    return id_lote

if __name__ == "__main__":
    # RUTA CORREGIDA: Busca directamente en la carpeta data desde donde estás parado
    filepath = r"C:\Users\PC\Downloads\vitasoft-nosql\data\pagos_input.xlsx"
    
    datos = extract_data(filepath)
    if datos is not None:
        datos_limpios = transform_data(datos)
        load_to_mongodb(datos_limpios)
