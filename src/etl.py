"""
etl.py
Módulo de Extracción, Transformación y Carga (ETL) para Baguer S.A.S.
Responsable de procesar datos crudos y generar la base analítica (modelo estrella).

Salidas en data/processed/:
  - fact_inventario.csv  : ventas + inventario por tienda/sku/talla/fecha
  - dim_tienda.csv       : dimensión de tiendas
  - dim_producto.csv     : dimensión de productos con estado_curva
  - dim_fecha.csv        : dimensión de calendario
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(BASE_DIR, '..', 'data', 'raw')
PROCESSED_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed')


def extraer_datos(nombre_archivo):
    """Extrae un archivo CSV desde la carpeta raw y retorna un DataFrame."""
    ruta = os.path.join(RAW_PATH, nombre_archivo)
    try:
        df = pd.read_csv(ruta)
        print(f"[ETL] {nombre_archivo} cargado: {len(df)} filas.")
        return df
    except Exception as e:
        print(f"[ETL][ERROR] No se pudo cargar {nombre_archivo}: {e}")
        return pd.DataFrame()


def transformar_ventas(df):
    """Limpia y tipifica el DataFrame de ventas."""
    df = df.copy()
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['cantidad_vendida'] = pd.to_numeric(df['cantidad_vendida'], errors='coerce').fillna(0).astype(int)
    df['sku'] = df['sku'].astype(str)
    df['tienda_id'] = df['tienda_id'].astype(int)
    df['talla'] = df['talla'].astype(str).str.strip()
    return df


def transformar_inventario(df):
    """Limpia y tipifica el DataFrame de inventario."""
    df = df.copy()
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['cantidad_stock'] = pd.to_numeric(df['cantidad_stock'], errors='coerce').fillna(0).astype(int)
    df['sku'] = df['sku'].astype(str)
    df['tienda_id'] = df['tienda_id'].astype(int)
    df['talla'] = df['talla'].astype(str).str.strip()
    return df


def transformar_tiendas(df):
    """Limpia el DataFrame de tiendas."""
    df = df.copy()
    df['tienda_id'] = df['tienda_id'].astype(int)
    df['clima'] = df['clima'].str.strip()
    df['cargue'] = df['cargue'].str.strip()
    return df


def transformar_catalogo(df):
    """Limpia el DataFrame de catálogo y calcula estado_curva."""
    df = df.copy()
    df['sku'] = df['sku'].astype(str)
    df['marca'] = df['marca'].str.strip()
    df['categoria'] = df['categoria'].str.strip()
    # Estado_Curva = True si las tallas centrales M y L están disponibles
    tallas_centrales = {'M', 'L'}
    df['estado_curva'] = df['tallas_disponibles'].apply(
        lambda t: tallas_centrales.issubset(set(str(t).split('|')))
    )
    return df


def construir_fact_inventario(df_ventas, df_inventario):
    """
    Une ventas e inventario en una tabla de hechos unificada.
    Granularidad: tienda_id - sku - talla - fecha.
    Agrega inventario_inicial por tienda/sku/talla (stock del primer día).
    """
    keys = ['fecha', 'tienda_id', 'sku', 'talla']
    df_fact = pd.merge(df_inventario, df_ventas, on=keys, how='left')
    df_fact['cantidad_vendida'] = df_fact['cantidad_vendida'].fillna(0).astype(int)
    df_fact = df_fact.sort_values('fecha')

    # Inventario inicial = stock del primer día disponible por combinación
    primer_stock = (
        df_fact.groupby(['tienda_id', 'sku', 'talla'])['cantidad_stock']
        .first()
        .reset_index()
        .rename(columns={'cantidad_stock': 'inventario_inicial'})
    )
    df_fact = pd.merge(df_fact, primer_stock, on=['tienda_id', 'sku', 'talla'], how='left')
    print(f"[ETL] fact_inventario construida: {len(df_fact)} filas.")
    return df_fact


def construir_dim_fecha(df_fact):
    """Genera la dimensión de fechas con atributos de calendario."""
    fechas = df_fact['fecha'].drop_duplicates().sort_values().reset_index(drop=True)
    df_fecha = pd.DataFrame({'fecha': fechas})
    df_fecha['anio'] = df_fecha['fecha'].dt.year
    df_fecha['mes'] = df_fecha['fecha'].dt.month
    df_fecha['dia'] = df_fecha['fecha'].dt.day
    df_fecha['dia_semana'] = df_fecha['fecha'].dt.dayofweek  # 0 = lunes
    df_fecha['nombre_mes'] = df_fecha['fecha'].dt.strftime('%B')
    return df_fecha


def cargar_datos(df, nombre_archivo):
    """Guarda un DataFrame como CSV en la carpeta processed."""
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    ruta = os.path.join(PROCESSED_PATH, nombre_archivo)
    try:
        df.to_csv(ruta, index=False)
        print(f"[ETL] Guardado: {nombre_archivo} ({len(df)} filas)")
    except Exception as e:
        print(f"[ETL][ERROR] No se pudo guardar {nombre_archivo}: {e}")


def pipeline_etl():
    """Orquesta el flujo ETL completo: extracción, transformación y carga."""
    print("[ETL] Iniciando pipeline ETL...")

    df_ventas_raw = extraer_datos('ventas.csv')
    df_inv_raw = extraer_datos('inventario.csv')
    df_tiendas_raw = extraer_datos('tiendas.csv')
    df_catalogo_raw = extraer_datos('catalogo.csv')

    if df_ventas_raw.empty or df_inv_raw.empty:
        print("[ETL][ERROR] Faltan archivos críticos (ventas/inventario). Abortando.")
        return

    df_ventas = transformar_ventas(df_ventas_raw)
    df_inventario = transformar_inventario(df_inv_raw)
    df_tiendas = transformar_tiendas(df_tiendas_raw)
    df_catalogo = transformar_catalogo(df_catalogo_raw)

    df_fact = construir_fact_inventario(df_ventas, df_inventario)
    df_dim_fecha = construir_dim_fecha(df_fact)

    cargar_datos(df_fact, 'fact_inventario.csv')
    cargar_datos(df_tiendas, 'dim_tienda.csv')
    cargar_datos(df_catalogo, 'dim_producto.csv')
    cargar_datos(df_dim_fecha, 'dim_fecha.csv')

    print("[ETL] Pipeline ETL finalizado.")


if __name__ == "__main__":
    pipeline_etl()
