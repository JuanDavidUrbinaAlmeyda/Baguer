"""
kpi_engine.py
Módulo para el cálculo de KPIs de inventario y ventas en Baguer S.A.S.
Granularidad del resultado: tienda_id - sku - talla (resumen del período completo).

Salida en data/processed/:
  - kpis_resultado.csv  : KPIs + alertas por tienda/sku/talla
"""
import os
import pandas as pd
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed')

CONFIG_DIR = os.path.join(BASE_DIR, '..', 'config')
sys.path.insert(0, CONFIG_DIR)
from settings import CONFIG_SIMULACION  # noqa: E402

UMBRAL_QUIEBRE = CONFIG_SIMULACION['QUIEBRE_STOCK_DIAS']
UMBRAL_SOBRESTOCK = CONFIG_SIMULACION['SOBRESTOCK_DIAS']


def calcular_indice_rotacion(ventas, inventario_promedio):
    """Rotación = Ventas / Inventario Promedio"""
    return ventas / inventario_promedio if inventario_promedio > 0 else 0


def calcular_dias_inventario(inventario_final, ventas_diarias):
    """Días = Inventario Final / Ventas Diarias"""
    return inventario_final / ventas_diarias if ventas_diarias > 0 else 0


def calcular_sell_through(ventas, inventario_inicial):
    """Sell Through % = Ventas / Inventario Inicial"""
    return ventas / inventario_inicial if inventario_inicial > 0 else 0


def calcular_cobertura(inventario, demanda_esperada):
    """Cobertura = Inventario / Demanda Esperada"""
    return inventario / demanda_esperada if demanda_esperada > 0 else 0


def pipeline_kpis():
    """
    Lee fact_inventario.csv y calcula KPIs agregados por tienda/sku/talla.
    Guarda kpis_resultado.csv en data/processed/.
    """
    print("[KPI] Iniciando cálculo de KPIs...")

    ruta_fact = os.path.join(PROCESSED_PATH, 'fact_inventario.csv')
    try:
        df = pd.read_csv(ruta_fact, parse_dates=['fecha'])
    except Exception as e:
        print(f"[KPI][ERROR] No se pudo leer fact_inventario.csv: {e}")
        return

    df = df.sort_values('fecha')

    # Agregar por tienda / sku / talla
    grp = df.groupby(['tienda_id', 'sku', 'talla'])
    kpis = grp.agg(
        ventas_totales=('cantidad_vendida', 'sum'),
        inventario_promedio=('cantidad_stock', 'mean'),
        inventario_final=('cantidad_stock', 'last'),
        inventario_inicial=('inventario_inicial', 'first'),
        n_dias=('fecha', 'nunique'),
    ).reset_index()

    # Ventas diarias promedio
    kpis['ventas_diarias'] = kpis['ventas_totales'] / kpis['n_dias'].replace(0, 1)

    # Calcular KPIs
    kpis['rotacion'] = kpis.apply(
        lambda r: calcular_indice_rotacion(r['ventas_totales'], r['inventario_promedio']), axis=1
    )
    kpis['dias_inventario'] = kpis.apply(
        lambda r: calcular_dias_inventario(r['inventario_final'], r['ventas_diarias']), axis=1
    )
    # Sell-through mensual: fracción de stock vendida en los últimos 30 días
    # Definición correcta para retail: ventas_30d / inventario_promedio_30d
    # Valores esperados: sobrestock ~15-25%, normal ~55-75%, quiebre ~100%
    fecha_max = df['fecha'].max()
    df_30d = df[df['fecha'] > fecha_max - pd.Timedelta(days=30)]
    st_30d = df_30d.groupby(['tienda_id', 'sku', 'talla']).agg(
        _ventas_30d=('cantidad_vendida', 'sum'),
        _inv_prom_30d=('cantidad_stock', 'mean'),
    ).reset_index()
    kpis = kpis.merge(st_30d, on=['tienda_id', 'sku', 'talla'], how='left')
    kpis['sell_through_pct'] = (
        kpis['_ventas_30d'] / kpis['_inv_prom_30d'].replace(0, float('nan'))
    ).fillna(0)
    kpis = kpis.drop(columns=['_ventas_30d', '_inv_prom_30d'])

    kpis['cobertura_dias'] = kpis.apply(
        lambda r: calcular_cobertura(r['inventario_final'], r['ventas_diarias']), axis=1
    )

    # ── Limitar KPIs a rangos realistas (marco de 1 año de rotación máx.) ─────
    # dias_inventario / cobertura_dias: cap 365 días (1 año)
    # rotacion: cap 26 veces/año → ciclo mínimo de ~2 semanas (fast-fashion extremo)
    # sell_through_pct: cap 5.0 = 500 % (múltiples ciclos de reposición anuales)
    MAX_DIAS = 365
    MAX_ROTACION = 26.0
    MAX_SELL_THROUGH = 1.0   # 100% — sell-through mensual: no puede superar el stock disponible
    kpis['dias_inventario']  = kpis['dias_inventario'].clip(upper=MAX_DIAS)
    kpis['cobertura_dias']   = kpis['cobertura_dias'].clip(upper=MAX_DIAS)
    kpis['rotacion']         = kpis['rotacion'].clip(upper=MAX_ROTACION)
    kpis['sell_through_pct'] = kpis['sell_through_pct'].clip(upper=MAX_SELL_THROUGH)

    # Alertas según umbrales de settings.py
    kpis['alerta_quiebre'] = kpis['dias_inventario'] < UMBRAL_QUIEBRE
    kpis['alerta_sobrestock'] = kpis['dias_inventario'] > UMBRAL_SOBRESTOCK

    ruta_salida = os.path.join(PROCESSED_PATH, 'kpis_resultado.csv')
    kpis.round(4).to_csv(ruta_salida, index=False)

    n_quiebre = int(kpis['alerta_quiebre'].sum())
    n_sobre = int(kpis['alerta_sobrestock'].sum())
    print(f"[KPI] kpis_resultado.csv guardado: {len(kpis)} registros.")
    print(f"[KPI] Alertas -> Quiebre: {n_quiebre} | Sobrestock: {n_sobre}")
    print("[KPI] Pipeline de KPIs finalizado.")


if __name__ == "__main__":
    pipeline_kpis()
