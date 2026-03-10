# GUIA DE ARRANQUE — Sistema Analítico Baguer S.A.S.
> Fecha de referencia: Marzo 2026

---

## 1. Resumen Ejecutivo

El sistema automatiza la gestión de inventarios de **Baguer S.A.S.** (139 tiendas, +30 marcas de textil masculino). Su objetivo es reemplazar la gestión manual con un pipeline de datos que detecta sobrestock, anticipa quiebres de stock y sugiere traslados entre tiendas, todo explicado mediante narrativas en lenguaje natural.

**Metas:**
- Reducir sobrestock ≥ 20 %
- Aumentar rotación promedio ≥ 10 %

---

## 2. Arquitectura en Una Línea

```
Datos Crudos → ETL → KPIs → Forecast → Redistribución → Narrativas → Power BI
```

---

## 3. Orden de Ejecución (Prioridad)

| # | Archivo | Comando | Estado | Hace qué |
|---|---------|---------|--------|----------|
| **0** | `src/generar_datos_sinteticos.py` | `python src/generar_datos_sinteticos.py` | ✅ Funcional | Crea CSVs de prueba en `data/raw/` (tiendas, catálogo, ventas, inventario). Solo se corre **una vez** si no hay datos reales. |
| **1** | `src/etl.py` | `python src/etl.py` | ✅ Implementado | Lee `data/raw/`, transforma y guarda en `data/processed/` (modelo estrella). |
| **2** | `src/kpi_engine.py` | `python src/kpi_engine.py` | ✅ Implementado | Calcula Rotación, Días de Inventario, Sell-Through % y Cobertura. Genera alertas de quiebre/sobrestock. |
| **3** | `src/forecaster.py` | `python src/forecaster.py` | ✅ Implementado | Predice demanda a 30 días con RandomForest (sklearn). |
| **4** | `src/redistributor.py` | `python src/redistributor.py` | ✅ Implementado | Genera sugerencias de traslado y reporte de curvas de tallas incompletas. |
| **5** | `src/lm_explainer.py` | `python src/lm_explainer.py` | ✅ Implementado | Genera narrativas ejecutivas por tienda y JSON priorizado nacional. |
| **6** | `main.py` | `python main.py` | ✅ Orquestador | Corre los pasos 1–5 en secuencia. **Punto de entrada del pipeline diario.** |

> **✅ Implementado** = lógica real funcionando, produce archivos de salida.  
> **✅ Funcional** = corre sin errores y produce resultados.

---

## 4. Cómo Arrancar Desde Cero

### Paso 0 — Verificar dependencias
```bash
pip install pandas scikit-learn xgboost
```

### Paso 1 — Generar datos sintéticos (solo si no hay datos reales)
```bash
cd c:\Users\juanc\Documents\baguer
python src/generar_datos_sinteticos.py
```
Esto crea en `data/raw/`:
- `tiendas.csv` — 15 tiendas con clima y cargue
- `catalogo.csv` — 40 SKUs con tallas disponibles
- `ventas.csv` — 365 días × tiendas × SKUs × tallas
- `inventario.csv` — snapshot de stock por día

### Paso 2 — Correr el pipeline completo
```bash
python main.py
```
`main.py` ejecuta en orden: ETL → KPIs → Forecast → Redistribución → Narrativas.

### Paso 3 — Abrir el dashboard visual (opcional)
```bash
streamlit run dashboards/app.py
```
Abre http://localhost:8501 en el navegador. Incluye 6 secciones:
- 🏠 Resumen Nacional — KPI cards + gráficos nacionales
- 🚨 Alertas & KPIs — tabla filtrable + mapa de calor
- 📈 Forecast de Demanda — línea temporal por tienda/SKU/talla
- 🔄 Redistribución — traslados sugeridos + SKUs con curva incompleta
- 💬 Narrativas Ejecutivas — ranking de urgencia + texto ejecutivo por tienda
- ▶️ Ejecutar Pipeline — botón para lanzar `main.py` directamente desde el dashboard

---

## 5. Descripción de Cada Módulo

### `config/settings.py`
Diccionario central de reglas de negocio. **Modificar aquí, no en el código.**
```python
PERMANENCIA_MINIMA_DIAS = 30   # días en tienda antes de permitir traslado
QUIEBRE_STOCK_DIAS      = 10   # días de inventario = alerta quiebre
SOBRESTOCK_DIAS         = 90   # días de inventario = alerta sobrestock
```

### `src/etl.py`
Extrae archivos CSV de `data/raw/`, aplica transformaciones y los guarda en `data/processed/`.  
Genera el modelo estrella: `fact_inventario`, `dim_tienda`, `dim_producto`, `dim_fecha`.

### `src/kpi_engine.py`
Calcula 4 métricas clave:
- **Índice de Rotación** = Ventas / Inventario Promedio
- **Días de Inventario** = Inventario Final / Ventas Diarias
- **Sell-Through %** = Ventas / Inventario Inicial
- **Cobertura** = Inventario / Demanda Esperada

### `src/forecaster.py`
Modelo ML (Random Forest o XGBoost) que predice la demanda a 30 días.  
Considera clima de la tienda y cargue como variables.

### `src/redistributor.py`
Motor de reglas que:
1. Identifica tiendas con **sobrestock** (> 90 días)
2. Identifica tiendas en **riesgo de quiebre** (< 10 días)
3. Genera tabla de **sugerencias de traslado** (origen → destino, SKU, talla, cantidad)
4. Activa **unificación de tallas** cuando `Estado_Curva = False`

### `src/lm_explainer.py`
Convierte los resultados analíticos a JSON y los pasa a un modelo de lenguaje para generar:
- Narrativas ejecutivas por tienda
- Lista priorizada de alertas

### `dashboards/`
Directorio reservado para archivos `.pbix` de Power BI.  
Conectar a `data/processed/` como fuente de datos.

---

## 6. Flujo de Datos

```
data/raw/
  tiendas.csv
  catalogo.csv
  ventas.csv
  inventario.csv
        │
        ▼  [etl.py]
data/processed/
  fact_inventario.csv
  dim_tienda.csv
  dim_producto.csv
        │
        ▼  [kpi_engine.py]
  kpis_resultado.csv
        │
        ▼  [forecaster.py]
  forecast_demanda.csv
        │
        ▼  [redistributor.py]
  sugerencias_redistribucion.csv
        │
        ▼  [lm_explainer.py]
  narrativas_ejecutivas.json
        │
        ▼  [Power BI]
  Dashboard ejecutivo
```

---

## 7. Estado Actual del Proyecto

| Módulo | Estructura | Lógica | Conectado a main.py |
|--------|-----------|--------|---------------------|
| `generar_datos_sinteticos.py` | ✅ | ✅ | No (manual) |
| `etl.py` | ✅ | ✅ | ✅ (activo) |
| `kpi_engine.py` | ✅ | ✅ | ✅ (activo) |
| `forecaster.py` | ✅ | ✅ | ✅ (activo) |
| `redistributor.py` | ✅ | ✅ | ✅ (activo) |
| `lm_explainer.py` | ✅ | ✅ | ✅ (activo) |
| `main.py` | ✅ | ✅ | — |
| `settings.py` | ✅ | ✅ | ✅ usado en kpi_engine, redistributor |

> **Estado actual:** pipeline completamente operativo. `python main.py` ejecuta el ciclo completo de principio a fin.  
> **Próximo paso sugerido:** conectar `data/processed/` como fuente de datos en Power BI (carpeta `dashboards/`).

---

## 8. Archivos de Referencia

| Archivo | Propósito |
|---------|-----------|
| [README.md](README.md) | Contexto de negocio y arquitectura general |
| [src/DOCUMENTACION.md](src/DOCUMENTACION.md) | Índice de documentación técnica por módulo |
| [config/settings.py](config/settings.py) | Umbrales y reglas de negocio configurables |
| [src/etl.md](src/etl.md) | Documentación detallada del ETL |
| [src/forecaster.md](src/forecaster.md) | Documentación del modelo de predicción |
| [src/redistributor.md](src/redistributor.md) | Documentación del motor de redistribución |
| [src/lm_explainer.md](src/lm_explainer.md) | Documentación de narrativas ejecutivas |
