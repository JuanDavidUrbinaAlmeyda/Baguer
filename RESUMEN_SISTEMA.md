# Sistema Analítico de Inventarios — Baguer S.A.S.
> Documento de referencia ejecutiva · Marzo 2026

---

## ¿Qué es este sistema?

Un pipeline de datos que reemplaza la gestión manual de inventarios de **Baguer S.A.S.** (139 tiendas, +30 marcas de textil masculino). Detecta automáticamente sobrestock y quiebres de stock, sugiere traslados entre tiendas, predice demanda a 30 días y genera narrativas ejecutivas por tienda.

**Metas de negocio:**
- Reducir sobrestock ≥ 20 %
- Aumentar rotación promedio ≥ 10 %

---

## Cómo arrancar

```bash
# 1. Activar entorno virtual
.venv\Scripts\activate

# 2. Solo si no hay datos reales — generar datos sintéticos
python src/generar_datos_sinteticos.py

# 3. Correr el pipeline completo
python main.py

# 4. Abrir el dashboard
streamlit run dashboards/app.py
# → http://localhost:8501
```

---

## Arquitectura del Pipeline

```
data/raw/                        data/processed/
  tiendas.csv    ──┐
  catalogo.csv   ──┤  [1. etl.py]  ──►  fact_inventario.csv
  ventas.csv     ──┤                     dim_tienda.csv
  inventario.csv ──┘                     dim_producto.csv
                                         dim_fecha.csv
                                              │
                                   [2. kpi_engine.py]
                                              │
                                         kpis_resultado.csv
                                         (2 385 registros)
                                              │
                                   [3. forecaster.py]
                                              │
                                         forecast_demanda.csv
                                         (71 550 predicciones)
                                              │
                                   [4. redistributor.py]
                                              │
                                    sugerencias_redistribucion.csv
                                    tallas_unificar.csv
                                              │
                                   [5. lm_explainer.py]
                                              │
                                    narrativas_ejecutivas.json
                                              │
                                   [dashboards/app.py]
                                    http://localhost:8501
```

---

## Los 5 Módulos del Pipeline

### 1. `src/etl.py` — Extracción y Transformación
Lee los 4 CSVs de `data/raw/`, limpia tipos de datos, construye el **modelo estrella** y calcula `estado_curva` (True si el SKU tiene tallas M y L disponibles).

**Salidas:** `fact_inventario.csv`, `dim_tienda.csv`, `dim_producto.csv`, `dim_fecha.csv`

---

### 2. `src/kpi_engine.py` — Motor de KPIs
Agrega `fact_inventario` por Tienda × SKU × Talla y calcula 4 métricas clave:

| KPI | Fórmula | Alarma |
|-----|---------|--------|
| **Días de Inventario** | Stock final ÷ Ventas diarias | 🔴 < 10 días = Quiebre · 🟡 > 90 días = Sobrestock |
| **Índice de Rotación** | Ventas totales ÷ Inventario promedio | Bajo = producto parado |
| **Sell-Through %** | Ventas ÷ Inventario inicial | Cerca de 100% = casi sin stock |
| **Cobertura** | Stock ÷ Demanda esperada | Días que dura el stock al ritmo forecast |

Los umbrales (10 y 90 días) se configuran en `config/settings.py`.

**Salida:** `kpis_resultado.csv`

---

### 3. `src/forecaster.py` — Predicción de Demanda
Entrena un **Random Forest** con 365 días históricos y genera demanda diaria predicha para los próximos 30 días.

**Features del modelo:** `tienda_id`, `sku`, `talla`, `clima`, `cargue`, `mes`, `dia_semana`

**Salida:** `forecast_demanda.csv` (una fila por Tienda × SKU × Talla × Día)

---

### 4. `src/redistributor.py` — Motor de Redistribución
Cruza las listas de sobrestock y quiebre: para cada tienda en quiebre busca una tienda origen con sobrestock del mismo SKU y talla.

**Lógica de cantidad sugerida:**
$$\text{cantidad} = \min\left(\text{ventas\_diarias\_destino} \times 30,\; \text{stock\_origen} \times 0.5\right)$$

También genera `tallas_unificar.csv`: SKUs donde falta M o L (curva incompleta), que bloquean ventas activamente.

**Salidas:** `sugerencias_redistribucion.csv`, `tallas_unificar.csv`

---

### 5. `src/lm_explainer.py` — Narrativas Ejecutivas
Convierte los KPIs de cada tienda en texto ejecutivo legible y calcula un resumen nacional. No requiere API externa.

**Salida:** `narrativas_ejecutivas.json`

---

## El Dashboard — 6 Pestañas

### 🏠 Resumen Nacional
Vista macro. **¿Cómo está el país hoy?**
- 4 KPI cards: alertas de quiebre, alertas de sobrestock, rotación promedio nacional, SKUs con curva incompleta.
- Barra de **alertas por tienda** — si siempre son las mismas, el problema es estructural.
- **Scatter Días de Inventario vs Rotación** — el gráfico más importante: las tiendas en la esquina superior-izquierda tienen sobrestock crónico.

---

### 🚨 Alertas & KPIs
Drill-down filtrable. **¿Qué SKU específico, en qué tienda, está en problema?**
- Filtros por tienda, SKU, talla y tipo de alerta.
- Tabla con colores: 🔴 Quiebre · 🟡 Sobrestock · 🟢 OK.
- **Mapa de calor Tienda × Talla**: si una talla está roja en todas las tiendas, el problema es de compra, no de distribución.

---

### 📈 Forecast de Demanda
**¿Cuánto voy a necesitar el próximo mes?**
- Selector Tienda / SKU / Talla → línea temporal de demanda predicha.
- Cards: demanda total 30 días y promedio diario.
- Barra de demanda total por tienda: identifica qué tiendas van a presionar más el stock.

---

### 🔄 Redistribución
**¿Qué muevo, de dónde, a dónde y cuánto?**
- Tabla de traslados sugeridos con origen, destino, SKU, talla, cantidad y días de cobertura de cada parte.
- Tabla de SKUs con curva incompleta (sin M o L) — primera prioridad antes de cualquier traslado.
- Si un SKU aparece muchas veces, el problema es de asignación inicial en compras, no de ventas.

---

### 💬 Narrativas Ejecutivas
**¿Qué le digo al gerente regional?**
- Resumen nacional en 4 KPI cards.
- Selector de tienda → texto ejecutivo + métricas detalladas.
- **Ranking de urgencia**: 🔴 Crítica (> 5 alertas) · 🟡 Moderada · 🟢 Óptima.

---

### ▶️ Ejecutar Pipeline
**Panel operativo.**
- Botón para lanzar `main.py` directamente desde el browser con output en tiempo real.
- Botón para regenerar datos sintéticos.
- Tabla de **Estado de Archivos**: si `sugerencias_redistribucion.csv` aparece como ❌ Falta, no hubo ningún par sobrestock↔quiebre matcheable (mismo SKU, misma talla, distinta tienda).

---

## Reglas de Negocio Configurables

Todas en `config/settings.py`. **Modificar aquí, nunca hardcodeado.**

| Parámetro | Valor actual | Efecto |
|-----------|-------------|--------|
| `QUIEBRE_STOCK_DIAS` | 10 días | Umbral mínimo de cobertura |
| `SOBRESTOCK_DIAS` | 90 días | Umbral máximo de cobertura |
| `PERMANENCIA_MINIMA_DIAS` | 30 días | Días mínimos en tienda antes de trasladar |
| `UNIFICACION_TALLAS_ESTADO_CURVA` | False | Activa unificación si falta M o L |

---

## Estado Actual del Proyecto

| Módulo | Estado | Notas |
|--------|--------|-------|
| `generar_datos_sinteticos.py` | ✅ Funcional | Genera perfiles sobrestock/quiebre/normal |
| `etl.py` | ✅ Funcional | Modelo estrella completo |
| `kpi_engine.py` | ✅ Funcional | 4 KPIs + alertas con umbrales de settings |
| `forecaster.py` | ✅ Funcional | Random Forest, features clima y cargue |
| `redistributor.py` | ✅ Funcional | 658 traslados generados en última corrida |
| `lm_explainer.py` | ✅ Funcional | Narrativas sin API externa |
| `main.py` | ✅ Funcional | Orquesta los 5 pasos en secuencia |
| `dashboards/app.py` | ✅ Funcional | Streamlit + Plotly, 6 pestañas |

---

## Cifras de la Última Ejecución (Marzo 9, 2026 — Datos Sintéticos)

| Métrica | Valor |
|---------|-------|
| Tiendas simuladas | 15 |
| SKUs en catálogo | 40 |
| Días históricos | 365 |
| Filas en fact_inventario | 870,525 |
| Registros KPI | 2,385 |
| Alertas de quiebre | 706 |
| Alertas de sobrestock | 488 |
| Predicciones forecast | 71,550 |
| Traslados sugeridos | 658 |
| SKUs curva incompleta | 12 |
| Rotación nacional promedio | 196.79 |

---

## Guía Rápida de Diagnóstico

| Síntoma | Dónde mirar | Interpretación |
|---------|-------------|----------------|
| Mismas tiendas siempre en quiebre | 🏠 Resumen · barra alertas | Problema estructural de reposición |
| Una talla roja en todas las tiendas | 🚨 Alertas · heatmap | Error de compra en esa talla |
| SKU aparece muchas veces en traslados | 🔄 Redistribución · tabla | Asignación inicial desequilibrada en compras |
| `sugerencias_redistribucion.csv` vacío | ▶️ Pipeline · estado archivos | No hay pares sobrestock↔quiebre con mismo SKU/talla |
| Forecast casi plano sin estacionalidad | 📈 Forecast · gráfico | El modelo necesita features de temporada o precio |
| Rotación muy alta (> 100) | 💬 Narrativas · ranking | Stock casi agotado, sell-through cercano a 100% |

---

## Próximos Pasos Sugeridos

1. **Conectar datos reales** — reemplazar los CSVs de `data/raw/` con exportaciones del ERP de Baguer.
2. **Agregar estacionalidad al forecast** — incorporar indicadores de temporada alta/baja y días festivos como features.
3. **Precio como variable** — agregar `precio_unitario` al catálogo para calcular valor en riesgo ($) además de unidades.
4. **Automatización diaria** — programar `main.py` como tarea programada (Windows Task Scheduler o cron) para que corra cada noche.
5. **Conectar Power BI** — apuntar los archivos de `data/processed/` como fuente de datos en `dashboards/` para reportes ejecutivos adicionales.
