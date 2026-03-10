# kpi_engine - Motor de KPIs

## Objetivo
Calcular indicadores clave de inventario y ventas para la toma de decisiones.

## KPIs principales
- Índice de Rotación
- Días de Inventario
- Sell Through %
- Cobertura
- Permanencia en tienda

## Entradas
- fact_inventario.csv (procesado)
- dim_tienda.csv
- dim_producto.csv
- dim_fecha.csv

## Salidas
- kpis_tienda_sku_talla.csv (por tienda, SKU, talla, día)

## Pasos principales
1. **Cálculo de KPIs:** Usar fórmulas estándar y reglas de negocio.
2. **Validación:** Revisar valores extremos y consistencia.
3. **Exportación:** Guardar resultados para análisis y visualización.

## Consideraciones
- Documentar cada fórmula y función.
- Permitir ajuste de umbrales desde settings.py.

---

> Actualizar este documento con fórmulas y ejemplos a medida que avance el desarrollo.
