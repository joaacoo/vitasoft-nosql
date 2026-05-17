import os
from pymongo import MongoClient

# Configuración MongoDB
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "vitasoft_db"
OUTPUT_DIR = r"C:\Users\PC\Downloads\vitasoft-nosql\data\output"

def generar_txt_bancario(id_lote: str):
    """
    Genera un archivo TXT con el formato bancario estándar para un lote de pagos.
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Buscar el lote
    lote = db.lotes_pago.find_one({"id_lote": id_lote})
    
    if not lote:
        print(f"Lote {id_lote} no encontrado.")
        client.close()
        return None
        
    # Asegurar que el directorio de salida existe
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    filename = os.path.join(OUTPUT_DIR, f"banco_export_{id_lote}.txt")
    
    with open(filename, "w", encoding="utf-8") as file:
        # Cabecera del archivo bancario
        fecha_str = lote["fecha_proceso"].strftime("%Y%m%d")
        total_monto = sum(p["monto"] for p in lote["pagos"])
        cantidad = lote["cantidad_registros"]
        
        # Formato de cabecera: H + Fecha(8) + Cantidad(6) + Total(15) + LoteID(36)
        header = f"H{fecha_str}{str(cantidad).zfill(6)}{f'{total_monto:.2f}'.zfill(15)}{id_lote}\n"
        file.write(header)
        
        # Detalle de pagos
        for p in lote["pagos"]:
            cuit = str(p.get("cuit", "")).replace("-", "").ljust(11)
            cbu = str(p.get("cbu", "")).zfill(22)
            monto = f"{p.get('monto', 0):.2f}".zfill(15)
            nombre = str(p.get("proveedor", ""))[:30].ljust(30)
            
            # Formato de detalle: D + CUIT(11) + CBU(22) + Monto(15) + Nombre(30)
            detalle = f"D{cuit}{cbu}{monto}{nombre}\n"
            file.write(detalle)
            
        # Pie de archivo
        file.write(f"T{fecha_str}{str(cantidad).zfill(6)}\n")
        
    # Actualizar el historial del lote en MongoDB
    db.lotes_pago.update_one(
        {"id_lote": id_lote},
        {"$push": {
            "historial": {
                "fecha": lote["fecha_proceso"],  # Se podría usar datetime.datetime.now()
                "accion": "exportacion_txt",
                "detalle": f"Archivo TXT generado: {filename}"
            }
        }}
    )
    
    client.close()
    print(f"Archivo bancario generado exitosamente en: {filename}")
    return filename

if __name__ == "__main__":
    # Prueba manual: Si se corre este script directamente, intenta exportar el último lote
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    ultimo_lote = db.lotes_pago.find_one(sort=[("fecha_proceso", -1)])
    client.close()
    
    if ultimo_lote:
        generar_txt_bancario(ultimo_lote["id_lote"])
    else:
        print("No hay lotes en la base de datos para exportar.")
