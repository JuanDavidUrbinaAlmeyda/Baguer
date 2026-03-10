# Resultados del Sistema Analítico de Inventarios
> Baguer S.A.S. · Simulación con datos sintéticos · Marzo 2026

---

## 1. Alcance de la Simulación

| Parámetro | Valor |
|---|---|
| Período analizado | 365 días (1 año) |
| Tiendas | 15 |
| SKUs en catálogo | 40 |
| Tallas por SKU | 3 a 5 (S, M, L, XL, XXL) |
| Combinaciones Tienda × SKU × Talla analizadas | **2 355** |
| Registros históricos (fact_inventario) | ~860 000 |

---

## 2. Indicadores Clave de Inventario (KPIs)

### 2.1 Panorama Nacional

| KPI | Valor |
|---|---|
| **Rotación promedio** | **10.72 veces/año** (ciclo ~34 días) |
| Días de inventario (mediana) | 65.2 días |
| Sell-through mensual (mediana) | 45.6 % |
| Alertas de **quiebre de stock** | **715 SKU/talla** — 30.4 % del total |
| Alertas de **sobrestock** | **444 SKU/talla** — 18.9 % del total |
| SKU/talla en estado **normal** | 1 196 — 50.8 % del total |

### 2.2 Distribución por Perfil de Inventario

| Perfil | Registros | Días inv. (med.) | Rotación (med.) | Sell-through mensual (med.) |
|---|---|---|---|---|
| **Normal** *(objetivo)* | 1 196 (50.8 %) | 68.9 días | 5.31 ×/año | 44.1 % |
| **Quiebre** *(crítico)* | 715 (30.4 %) | 2.4 días | 26.0 ×/año *(cap)* | 100 % *(siempre agotado)* |
| **Sobrestock** *(ineficiente)* | 444 (18.9 %) | 365 días *(cap)* | 0.67 ×/año | 5.5 % |

> **Interpretación:** 1 de cada 3 combinaciones está en quiebre activo; casi 1 de cada 5 tiene stock inmovilizado por más de 3 meses. Solo la mitad opera dentro del rango saludable (15–90 días de cobertura).

---

## 3. Análisis de Alertas por Tienda

### 3.1 Tiendas con Mayor Riesgo de Quiebre

| Posición | Tienda | SKU/talla en quiebre |
|---|---|---|
| 1 | Tienda_13 | 54 |
| 2 | Tienda_11 | 53 |
| 3 | Tienda_10 | 51 |
| 4 | Tienda_14 | 51 |
| 5 | Tienda_5 | 51 |

> Las tiendas con mayor quiebre representan oportunidades de venta perdida diaria. Una tienda con 54 SKU/talla en quiebre no puede atender demanda en el 30 % de su surtido.

### 3.2 Tiendas con Mayor Acumulación de Sobrestock

| Posición | Tienda | SKU/talla con sobrestock |
|---|---|---|
| 1 | Tienda_4 | 34 |
| 2 | Tienda_9 | 34 |
| 3 | Tienda_2 | 32 |
| 4 | Tienda_8 | 31 |
| 5 | Tienda_12 | 31 |

---

## 4. Motor de Redistribución — Sugerencias de Traslado

El motor cruza los perfiles de quiebre y sobrestock para proponer traslados inteligentes entre tiendas del mismo SKU/talla.

| Indicador | Valor |
|---|---|
| **Traslados sugeridos** | **642** |
| **Unidades totales a mover** | **38 072 unidades** |
| SKUs involucrados | 40 (todos) |
| Lógica de cantidad | Cubre 30 días de demanda del destino, máximo 50 % del stock disponible en origen |

> **Impacto potencial:** Si se ejecutan los 642 traslados, se resuelven al menos parcialmente 642 situaciones de quiebre activo, movilizando inventario inmovilizado hacia donde genera venta real.

---

## 5. Forecast de Demanda — Próximos 30 Días

Modelo: **Random Forest Regressor** entrenado sobre 365 días de historia.

Features: tienda, SKU, talla, clima, nivel de cargue, mes, día de semana.

| Indicador | Valor |
|---|---|
| Horizonte de predicción | 30 días |
| Combinaciones predichas | 2 355 (todas las activas) |
| **Demanda total proyectada** | **80 629 unidades** |
| **Demanda diaria promedio** | **~2 688 unidades/día** |

---

## 6. Análisis de Curva de Tallas

| Indicador | Valor |
|---|---|
| SKUs con curva **completa** (tienen M y L) | 25 de 40 |
| SKUs con curva **incompleta** | **15 SKUs** |
| Categorías afectadas | Camisa: 5 · Pantalón: 5 · Chaqueta: 5 |

> Un SKU sin talla M o L pierde ventas en las tallas de mayor demanda. Los 15 SKUs identificados son candidatos a gestión de reposición prioritaria o unificación de surtido.

---

## 7. Factores Externos: Clima y Nivel de Cargue

### Rotación por Clima (veces/año)

| Clima | Media | Mediana |
|---|---|---|
| Templado | 11.03 | 5.39 |
| Cálido | 10.67 | 5.36 |
| Frío | 10.60 | 5.36 |

> La variación por clima es baja (~4 %), lo que indica que el surtido actual **no está diferenciado** por condición climática. Oportunidad de personalización.

### Días de Inventario por Nivel de Cargue

| Cargue | Media | Mediana |
|---|---|---|
| Bajo | 106.2 días | 64.8 días |
| Alto | 104.2 días | 66.0 días |
| Medio | 102.4 días | 64.0 días |

> No hay diferencia significativa entre niveles de cargue, lo que sugiere que **la asignación inicial de stock no está calibrada por capacidad de venta** de cada tienda.

---

## 8. Diagnóstico y Propuestas

### Diagnóstico General
- **30 % de quiebre activo** implica ventas perdidas constantes. En retail de moda, un quiebre de 3 días puede representar pérdida permanente (el cliente compra en otro lado).
- **18.9 % de sobrestock** implica capital inmovilizado, riesgo de obsolescencia y presión sobre descuentos al cierre de temporada.
- **La rotación de 10.72 ×/año** es razonable para moda masculina (rango típico: 8–15 ×/año), pero convive con extremos muy distantes entre tiendas.

### Propuestas del Sistema

| # | Propuesta | Módulo | Impacto |
|---|---|---|---|
| 1 | Ejecutar los **642 traslados sugeridos** entre tiendas | `redistributor.py` | Convierte stock inmovilizado en ventas, resuelve quiebres sin nueva compra |
| 2 | Revisar los **15 SKUs con curva incompleta** y gestionar reposición de tallas M/L | `redistributor.py` | Recuperar ventas en la talla de mayor volumen |
| 3 | Usar el **forecast de 30 días** para planear órdenes de compra | `forecaster.py` | 80 629 unidades proyectadas = base objetiva para negociación con proveedores |
| 4 | **Diferenciar surtido por clima** — actualmente sin efecto medible | Configuración | Reducir sobrestock estacional en tiendas frías con productos de clima cálido |
| 5 | **Calibrar asignación inicial** por nivel de cargue de tienda | `generar_datos_sinteticos.py` / datos reales | Evitar sobrestock en tiendas de cargue bajo y quiebres en tiendas de cargue alto |
| 6 | Establecer **permanencia mínima de 30 días** antes de trasladar | `settings.py` | Evitar traslados prematuros que generen inestabilidad logística |

---

## 9. Marco de Umbrales Operativos

Definidos en `config/settings.py`:

| Umbral | Valor | Significado |
|---|---|---|
| `QUIEBRE_STOCK_DIAS` | < 10 días | Alerta de ruptura inminente |
| `SOBRESTOCK_DIAS` | > 90 días | Stock inmovilizado por más de 3 meses |
| `PERMANENCIA_MINIMA_DIAS` | 30 días | Tiempo mínimo en tienda antes de trasladar |
| `dias_inventario` máximo | 365 días | Cap operativo = 1 año de rotación |
| `rotacion` máxima | 26 ×/año | Cap estadístico = ciclo bi-semanal |
| `sell_through` mensual máximo | 100 % | Cap natural = no se puede vender más de lo que hay |

---

*Generado con datos sintéticos representativos — pipeline Baguer S.A.S. · Marzo 2026*
