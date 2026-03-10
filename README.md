---
title: Baguer Dashboard
emoji: 👔
colorFrom: indigo
colorTo: blue
sdk: streamlit
sdk_version: "1.35.0"
app_file: dashboards/app.py
pinned: false
---

## Estructura del Proyecto

- **config/**: Configuración y umbrales de negocio.
- **data/**: Datos crudos y procesados.
- **src/**: Scripts ETL, analíticos y de reglas.
- **dashboards/**: Visualización ejecutiva (Power BI).
- **main.py**: Orquestador del pipeline diario.

Para detalles técnicos, consulta la documentación en src/DOCUMENTACION.md.

---

## README: Sistema Analítico de Optimización de Inventarios - Baguer S.A.S.

1. Contexto del Proyecto

Este sistema busca transformar la gestión manual de inventarios en Baguer S.A.S. (139 tiendas, +30 marcas de textil masculino) en una estrategia proactiva basada en datos. El núcleo es un modelo analítico que automatiza la reposición, gestiona traslados entre tiendas y unifica curvas de tallas para maximizar la rentabilidad.

2. Reglas de Negocio y Umbrales (Modificables)

El sistema debe operar bajo un diccionario de configuración (settings.py) para evitar valores hardcodeados:

- Permanencia Mínima: 30 días en tienda antes de cualquier traslado.
- Quiebre de Stock: Menos de 10 días de inventario.
- Sobrestock: Más de 90 días de inventario.
- Unificación de Tallas: Se activa si el Estado_Curva es falso (faltan tallas centrales).
- Factores Críticos: La demanda debe verse afectada por el Clima (Cálido, Templado, Frío) y el Cargue de la tienda.

3. Arquitectura del Sistema

El proyecto se divide en las siguientes capas modulares:

- **A. Capa de Datos (ETL & Persistencia)**

  Entradas: Ventas históricas, Inventario actual (Tienda/Bodega), Catálogo y Tiendas.

  Modelo Estrella: Tablas de hechos (fact_inventario) y dimensiones (dim_tienda, dim_producto, dim_fecha).

  Granularidad: Tienda - SKU - Talla - Día.

- **B. Motor Analítico (Python)**

  - `kpi_engine.py`: Calcula Índice de Rotación, Días de Inventario, Sell Through % y Cobertura.
  - `forecaster.py`: Predicción de demanda a 30 días usando Random Forest o XGBoost.
  - `redistributor.py`: Motor de reglas para generar sugerencias_redistribucion entre tiendas origen y destino.
  - `lm_explainer.py`: Capa de LM para generar narrativas ejecutivas y priorizar alertas.

- **C. Visualización (Power BI)**

  Dashboard ejecutivo con Panorama Nacional, Mapas de Calor de stock y simulaciones de escenarios optimizados.

4. Flujo de Simulación "Natural"

Para recolectar patrones reales, la simulación debe:

- Validar Clima: Penalizar ventas si el producto no coincide con el clima de la tienda.
- Simular Quiebres: Detener ventas de un SKU si las tallas centrales se agotan (Curva Incompleta).
- Ejecutar Traslados: Mover stock de tiendas con baja rotación (>30 días permanencia) a tiendas con riesgo de quiebre.

5. Métricas de Éxito

- Reducción $\ge 20\%$ en sobrestock.
- Incremento $\ge 10\%$ en rotación promedio.