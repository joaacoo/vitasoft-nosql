# VitaSoft - Procesamiento de Pagos Masivos & Detección de Fraude

VitaSoft es una plataforma diseñada para automatizar la gestión de pagos a proveedores exportados desde sistemas ERP, implementando arquitectura de **Persistencia Políglota** para la detección de fraude estructural.

## Arquitectura
`ERP (CSV/Excel) -> Python Pandas (ETL) -> MongoDB (Operativo) -> Python (Sync) -> Neo4j (Analítico)`

## Tecnologías Utilizadas
* **Backend & ETL:** Python 3, Pandas
* **Bases de Datos:** MongoDB (Documental), Neo4j (Grafos)
* **Infraestructura:** Docker & Docker Compose

## Instrucciones de Ejecución

1. **Levantar Infraestructura:**
   ```bash
   docker-compose up -d
   ```

2. **Instalar Dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar Pipeline ETL:**
   Procesa el CSV y guarda los lotes documentales en Mongo.
   ```bash
   cd src/etl && python etl_mongo.py
   ```

4. **Sincronizar Grafo Analítico:**
   Construye la red de proveedores, direcciones y CBUs.
   ```bash
   cd src/sync && python sync_neo4j.py
   ```

5. **Auditoría:**
   * Accede a MongoDB mediante Compass en `localhost:27017`
   * Accede al motor de fraude en Neo4j Browser: `http://localhost:7474` (neo4j / vitasoft2026)
