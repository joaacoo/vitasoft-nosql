use vitasoft_db;

// 1. Crear Índices para performance
db.proveedores.createIndex({ "cuit": 1 }, { unique: true });
db.lotes_pago.createIndex({ "fecha_proceso": -1 });

// 2. Pipeline: Total pagado por proveedor (Sumarizando dentro de los lotes)
db.lotes_pago.aggregate([
  { $unwind: "$pagos" },
  { $group: {
      _id: "$pagos.cuit",
      nombre: { $first: "$pagos.proveedor" },
      total_pagado: { $sum: "$pagos.monto" },
      cantidad_pagos: { $sum: 1 }
  }},
  { $sort: { total_pagado: -1 } }
]);

// 3. Pipeline: Concentración de pagos por Banco
db.lotes_pago.aggregate([
  { $unwind: "$pagos" },
  { $group: {
      _id: "$pagos.banco",
      volumen_dinero: { $sum: "$pagos.monto" }
  }},
  { $sort: { volumen_dinero: -1 } }
]);
