"""
redistributor.py
Motor de reglas para sugerir traslados de inventario y unificación de tallas.

Reglas de negocio (de settings.py):
  - Sobrestock : dias_inventario > SOBRESTOCK_DIAS (90)
  - Quiebre    : dias_inventario < QUIEBRE_STOCK_DIAS (10)
  - Permanencia mínima antes de trasladar: PERMANENCIA_MINIMA_DIAS (30)

Salidas en data/processed/:
  - sugerencias_redistribucion.csv : traslados sugeridos (origen → destino)
  - tallas_unificar.csv            : SKUs con curva de tallas incompleta
"""
import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed')

CONFIG_DIR = os.path.join(BASE_DIR, '..', 'config')
sys.path.insert(0, CONFIG_DIR)
from settings import CONFIG_SIMULACION  # noqa: E402

UMBRAL_SOBRESTOCK = CONFIG_SIMULACION['SOBRESTOCK_DIAS']
UMBRAL_QUIEBRE = CONFIG_SIMULACION['QUIEBRE_STOCK_DIAS']
PERMANENCIA_MINIMA = CONFIG_SIMULACION['PERMANENCIA_MINIMA_DIAS']


def identificar_sobrestock(df_kpis: pd.DataFrame, umbral: int = UMBRAL_SOBRESTOCK) -> pd.DataFrame:
    """Retorna filas con dias_inventario > umbral y stock disponible."""
    mask = (df_kpis['dias_inventario'] > umbral) & (df_kpis['inventario_final'] > 0)
    return df_kpis[mask].copy()


def identificar_quiebre(df_kpis: pd.DataFrame, umbral: int = UMBRAL_QUIEBRE) -> pd.DataFrame:
    """Retorna filas con dias_inventario < umbral (riesgo de quiebre)."""
    mask = (df_kpis['dias_inventario'] >= 0) & (df_kpis['dias_inventario'] < umbral)
    return df_kpis[mask].copy()


def sugerir_traslados(df_kpis: pd.DataFrame = None) -> pd.DataFrame:
    """
    Para cada tienda/sku/talla en quiebre, busca una tienda origen con sobrestock
    del mismo sku/talla y genera la sugerencia de traslado.
    La cantidad sugerida cubre ~30 días de demanda del destino,
    limitada al 50 % del stock disponible en el origen.
    """
    if df_kpis is None:
        try:
            df_kpis = pd.read_csv(os.path.join(PROCESSED_PATH, 'kpis_resultado.csv'))
        except Exception as e:
            print(f"[REDIS][ERROR] No se pudo leer kpis_resultado.csv: {e}")
            return pd.DataFrame()

    sobre = identificar_sobrestock(df_kpis)
    quiebre = identificar_quiebre(df_kpis)
    print(f"[REDIS] Sobrestock: {len(sobre)} registros | Quiebre: {len(quiebre)} registros")

    sugerencias = []
    for _, dest in quiebre.iterrows():
        candidatos = sobre[
            (sobre['sku'] == dest['sku']) &
            (sobre['talla'] == dest['talla']) &
            (sobre['tienda_id'] != dest['tienda_id'])
        ].sort_values('inventario_final', ascending=False)

        if candidatos.empty:
            continue

        origen = candidatos.iloc[0]
        demanda_diaria_dest = dest.get('ventas_diarias', 0)
        cantidad = int(min(
            demanda_diaria_dest * PERMANENCIA_MINIMA,   # cubrir 30 días
            origen['inventario_final'] * 0.5            # máximo 50 % del stock origen
        ))
        if cantidad <= 0:
            continue

        sugerencias.append({
            'sku': dest['sku'],
            'talla': dest['talla'],
            'tienda_origen': int(origen['tienda_id']),
            'tienda_destino': int(dest['tienda_id']),
            'cantidad_sugerida': cantidad,
            'dias_inventario_origen': round(float(origen['dias_inventario']), 1),
            'dias_inventario_destino': round(float(dest['dias_inventario']), 1),
        })

    df_sug = pd.DataFrame(sugerencias)
    if not df_sug.empty:
        ruta = os.path.join(PROCESSED_PATH, 'sugerencias_redistribucion.csv')
        df_sug.to_csv(ruta, index=False)
        print(f"[REDIS] sugerencias_redistribucion.csv guardado: {len(df_sug)} traslados sugeridos.")
    else:
        print("[REDIS] No se generaron sugerencias de traslado.")
    return df_sug


def unificar_tallas() -> None:
    """
    Identifica SKUs donde estado_curva=False (faltan tallas centrales M/L)
    y genera tallas_unificar.csv como reporte de acción.
    """
    try:
        df_prod = pd.read_csv(os.path.join(PROCESSED_PATH, 'dim_producto.csv'))
    except Exception as e:
        print(f"[REDIS][ERROR] No se pudo leer dim_producto.csv: {e}")
        return

    curva_incompleta = df_prod[~df_prod['estado_curva']][
        ['sku', 'marca', 'categoria', 'tallas_disponibles']
    ]
    if not curva_incompleta.empty:
        ruta = os.path.join(PROCESSED_PATH, 'tallas_unificar.csv')
        curva_incompleta.to_csv(ruta, index=False)
        print(f"[REDIS] tallas_unificar.csv: {len(curva_incompleta)} SKUs con curva incompleta.")
    else:
        print("[REDIS] Todos los SKUs tienen curva de tallas completa (M y L presentes).")


def pipeline_redistribucion():
    """Orquesta redistribución de inventario y detección de curvas incompletas."""
    print("[REDIS] Iniciando pipeline de redistribución...")
    sugerir_traslados()
    unificar_tallas()
    print("[REDIS] Pipeline de redistribución finalizado.")


if __name__ == "__main__":
    pipeline_redistribucion()
