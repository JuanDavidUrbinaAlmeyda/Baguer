# forecaster - Predicción de Demanda

## Objetivo
Predecir la demanda a 30 días para cada tienda, SKU y talla usando modelos de machine learning.

## Modelos sugeridos
- Random Forest
- XGBoost

## Entradas
- Datos procesados de ventas e inventario
- KPIs históricos
- Factores críticos: clima, cargue, eventos

## Salidas
- prediccion_demanda.csv (por tienda, SKU, talla, día)

## Pasos principales
1. **Preparación de datos:** Selección de variables y features.
2. **Entrenamiento:** Ajuste y validación de modelos.
3. **Predicción:** Generar demanda futura a 30 días.
4. **Exportación:** Guardar resultados para redistribución y visualización.

## Consideraciones
- Documentar hiperparámetros y métricas de evaluación.
- Permitir ajuste de horizonte de predicción.

---

> Actualizar este documento con detalles de implementación y ejemplos a medida que avance el desarrollo.
