"""
forecaster.py
Predicción de demanda a 30 días por tienda/sku/talla usando RandomForestRegressor.

Features: tienda_id, sku, talla, clima, cargue, mes, dia_semana.
Salida en data/processed/:
  - forecast_demanda.csv : demanda diaria predicha para los próximos 30 días
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed')

HORIZONTE_DIAS = 30
FEATURES = ['tienda_id', 'sku_enc', 'talla_enc', 'clima_enc', 'cargue_enc', 'mes', 'dia_semana']

# Almacén de encoders para reusar en predicción
_encoders: dict = {}


def _encode_col(df: pd.DataFrame, col: str, fit: bool = True) -> pd.DataFrame:
    """Codifica una columna categórica usando LabelEncoder."""
    enc_key = col
    if fit:
        le = LabelEncoder()
        df[col + '_enc'] = le.fit_transform(df[col].astype(str))
        _encoders[enc_key] = le
    else:
        le = _encoders[enc_key]
        # Manejar valores no vistos durante el entrenamiento
        df[col + '_enc'] = df[col].astype(str).map(
            lambda x: le.transform([x])[0] if x in le.classes_ else -1
        )
    return df


def preparar_datos():
    """
    Carga fact_inventario y dimensiones, construye el DataFrame de features.
    Retorna (df_features, df_tiendas).
    """
    fact = pd.read_csv(os.path.join(PROCESSED_PATH, 'fact_inventario.csv'), parse_dates=['fecha'])
    tiendas = pd.read_csv(os.path.join(PROCESSED_PATH, 'dim_tienda.csv'))

    df = fact.merge(tiendas[['tienda_id', 'clima', 'cargue']], on='tienda_id', how='left')
    df['mes'] = df['fecha'].dt.month
    df['dia_semana'] = df['fecha'].dt.dayofweek

    for col in ['sku', 'talla', 'clima', 'cargue']:
        df = _encode_col(df, col, fit=True)

    print(f"[FORECAST] Datos preparados: {len(df)} filas, {df['fecha'].nunique()} días.")
    return df, tiendas


def entrenar_modelo(df: pd.DataFrame) -> RandomForestRegressor:
    """Entrena un RandomForestRegressor con los datos históricos."""
    X = df[FEATURES]
    y = df['cantidad_vendida']
    modelo = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    modelo.fit(X, y)
    print(f"[FORECAST] Modelo entrenado con {len(X)} muestras.")
    return modelo


def predecir_demanda(modelo: RandomForestRegressor, df: pd.DataFrame, tiendas: pd.DataFrame) -> pd.DataFrame:
    """
    Genera predicción diaria a 30 días para cada combinación única tienda/sku/talla.
    """
    ultima_fecha = df['fecha'].max()

    # Base de combinaciones únicas con sus features estáticos
    base = (
        df[['tienda_id', 'sku', 'talla', 'sku_enc', 'talla_enc']]
        .drop_duplicates()
        .merge(tiendas[['tienda_id', 'clima', 'cargue']], on='tienda_id', how='left')
    )
    base = _encode_col(base, 'clima', fit=False)
    base = _encode_col(base, 'cargue', fit=False)

    registros = []
    for d in range(1, HORIZONTE_DIAS + 1):
        fecha_pred = ultima_fecha + timedelta(days=d)
        tmp = base.copy()
        tmp['fecha'] = fecha_pred
        tmp['mes'] = fecha_pred.month
        tmp['dia_semana'] = fecha_pred.dayofweek
        tmp['demanda_pred'] = np.maximum(
            0, modelo.predict(tmp[FEATURES]).round().astype(int)
        )
        registros.append(tmp[['fecha', 'tienda_id', 'sku', 'talla', 'demanda_pred']])

    df_forecast = pd.concat(registros, ignore_index=True)
    ruta = os.path.join(PROCESSED_PATH, 'forecast_demanda.csv')
    df_forecast.to_csv(ruta, index=False)
    print(f"[FORECAST] forecast_demanda.csv guardado: {len(df_forecast)} predicciones ({HORIZONTE_DIAS} días).")
    return df_forecast


def pipeline_forecast():
    """Orquesta el flujo completo de predicción de demanda."""
    print("[FORECAST] Iniciando pipeline de predicción...")
    try:
        df, tiendas = preparar_datos()
        modelo = entrenar_modelo(df)
        predecir_demanda(modelo, df, tiendas)
        print("[FORECAST] Pipeline de predicción finalizado.")
    except Exception as e:
        print(f"[FORECAST][ERROR] {e}")
        raise


if __name__ == "__main__":
    pipeline_forecast()
