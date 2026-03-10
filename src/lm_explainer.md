# lm_explainer - Generación de Narrativas Ejecutivas

## Objetivo
Transformar resultados analíticos en narrativas ejecutivas y alertas priorizadas para la toma de decisiones.

## Entradas
- Resultados de KPIs
- Sugerencias de redistribución
- Configuración de umbrales

## Salidas
- narrativas.json (resúmenes y alertas en lenguaje natural)

## Pasos principales
1. **Conversión de datos a JSON:** Estructurar resultados para entrada al modelo de lenguaje.
2. **Generación de narrativas:** Usar modelo de lenguaje para crear resúmenes y alertas.
3. **Priorización:** Destacar alertas críticas según reglas de negocio.
4. **Exportación:** Guardar narrativas para visualización y reporte.

## Consideraciones
- Documentar prompts y reglas de priorización.
- Permitir ajuste de criterios desde settings.py.

---

> Actualizar este documento con ejemplos y prompts a medida que avance el desarrollo.
