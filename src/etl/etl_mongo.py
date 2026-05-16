import pandas as pd
from pymongo import MongoClient
import datetime
import uuid

# Configuración MongoDB
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "vitasoft_db"

def extract_data(filepath):
    try:
        df = pd.read_csv(filepath)
        return df
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
        return None

def transform_data(df):
    # Normalización
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
        "pagos": []
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
        
        # Upsert en colección de proveedores para mantener padrón actualizado
        db.proveedores.update_one(
            {"cuit": row['cuit']},
            {"$set": {
                "nombre": row['proveedor'],
                "ultima_direccion": row['direccion'],
                "ultimo_cbu": row['cbu'],
                "fecha_actualizacion": fecha_proceso
            }},
            upsert=True
        )

    # Insertar el lote transaccional
    db.lotes_pago.insert_one(lote_doc)
    print(f"Lote {id_lote} cargado exitosamente en MongoDB. Registros: {len(df)}")
    client.close()

if __name__ == "__main__":
    filepath = "../../data/pagos_input.csv"
    data = extract_data(filepath)
    if data is not None:
        clean_data = transform_data(data)
        load_to_mongodb(clean_data)
