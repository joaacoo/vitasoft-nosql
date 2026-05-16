**¿Por qué Persistencia Políglota en VitaSoft?**
No existe una "bala de plata" en bases de datos.

* **MongoDB (Documental):** Optimizado para escrituras rápidas y volumen. Almacena el "lote de pago" completo como un documento único, evitando múltiples *inserts* relacionales. Es nuestra fuente de la verdad operativa (Sistema de Registro).
* **Neo4j (Grafos):** Extraemos solo las entidades (Proveedor, CBU, Dirección) para analizar relaciones. El modelo relacional (SQL) es ineficiente para detectar fraude en profundidad (requeriría múltiples auto-JOINs recursivos costosos). Neo4j usa *Index-Free Adjacency*, haciendo que los saltos entre nodos (traversals) tengan un costo constante, O(1), ideal para detectar redes sospechosas.

**CAP Theorem & Consistencia**

* **MongoDB** en un Replica Set prioriza **CP** (Consistencia y Tolerancia a Particiones). Mantiene consistencia fuerte en el nodo Primario para garantizar que los pagos no se dupliquen.
* La sincronización hacia Neo4j funciona como un esquema de consistencia eventual (BASE), donde el grafo se actualiza en micro-batches post-procesamiento.

**Escalabilidad**

* Para manejar grandes volúmenes de empresas pyme, MongoDB soporta *Sharding* (particionamiento horizontal basado en el `id_lote` o `fecha`), distribuyendo la carga de los archivos pesados del ERP.
