# Datos Sintéticos - Esquema y Generación

Este documento describe la estructura y lógica para crear datos sintéticos procesables por el pipeline.

## Archivos requeridos
- ventas.csv
- inventario.csv
- tiendas.csv
- catalogo.csv

## Esquema sugerido

### ventas.csv
- fecha (YYYY-MM-DD)
- tienda_id
- sku
- talla
- cantidad_vendida

### inventario.csv
- fecha (YYYY-MM-DD)
- tienda_id
- sku
- talla
- cantidad_stock

### tiendas.csv
- tienda_id
- nombre_tienda
- ciudad
- clima (Cálido/Templado/Frío)
- cargue (Alto/Medio/Bajo)

### catalogo.csv
- sku
- marca
- categoria
- descripcion
- tallas_disponibles (lista separada por |)

## Lógica de generación
- Generar 10-20 tiendas, 30-50 SKUs, 4-6 tallas por SKU.
- Fechas: último año (365 días).
- Ventas e inventario con variabilidad realista.
- Asignar clima y cargue a tiendas.
- Tallas centrales más frecuentes en ventas.

---

> Los scripts de generación deben crear estos archivos en data/raw/.
