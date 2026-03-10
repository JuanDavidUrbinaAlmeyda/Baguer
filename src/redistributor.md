# redistributor - Motor de Redistribución y Unificación de Tallas

## Objetivo
Sugerir traslados de inventario entre tiendas y activar la unificación de tallas cuando sea necesario.

## Entradas
- prediccion_demanda.csv
- KPIs calculados
- Configuración de umbrales (settings.py)

## Salidas
- sugerencias_redistribucion.csv (origen, destino, SKU, talla, cantidad)

## Pasos principales
1. **Identificación de sobrestock y quiebres:** Detectar tiendas con exceso o riesgo de quiebre.
2. **Reglas de traslado:** Sugerir movimientos de stock según permanencia, rotación y demanda esperada.
3. **Unificación de tallas:** Activar si faltan tallas centrales (Estado_Curva falso).
4. **Exportación:** Guardar sugerencias para ejecución y visualización.

## Consideraciones
- Documentar cada regla y condición.
- Permitir ajuste de umbrales desde settings.py.

---

> Actualizar este documento con reglas y ejemplos a medida que avance el desarrollo.
