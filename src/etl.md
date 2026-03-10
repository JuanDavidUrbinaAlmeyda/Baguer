# ETL - Extracción, Transformación y Carga

## Objetivo
Procesar y normalizar los datos crudos de ventas, inventario, tiendas y catálogo para alimentar el modelo analítico.

## Entradas
- data/raw/ventas.csv
- data/raw/inventario.csv
- data/raw/tiendas.csv
- data/raw/catalogo.csv

## Salidas
- data/processed/fact_inventario.csv
- data/processed/dim_tienda.csv
- data/processed/dim_producto.csv
- data/processed/dim_fecha.csv

## Pasos principales
1. **Extracción:** Leer archivos crudos desde data/raw.
2. **Transformación:** Limpiar, normalizar y validar datos. Unificar formatos y corregir inconsistencias.
3. **Carga:** Guardar datos procesados en data/processed siguiendo el modelo estrella.

## Consideraciones
- Validar claves foráneas y duplicados.
- Documentar cada función y transformación.
- Dejar logs de errores y advertencias.

---

> Este documento debe actualizarse con detalles de implementación y ejemplos de uso a medida que avance el desarrollo.
