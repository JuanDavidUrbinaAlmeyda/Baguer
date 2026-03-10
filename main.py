"""
main.py
Orquestador del pipeline diario para Baguer S.A.S.

Orden de ejecución:
  1. ETL           → data/processed/ (fact_inventario, dims)
  2. KPIs          → kpis_resultado.csv
  3. Forecast      → forecast_demanda.csv
  4. Redistribución → sugerencias_redistribucion.csv, tallas_unificar.csv
  5. Narrativas    → narrativas_ejecutivas.json

Uso:
  python main.py
"""
import sys
import os

# Agregar src al path para importar módulos
SRC_PATH = os.path.join(os.path.dirname(__file__), 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from etl import pipeline_etl
from kpi_engine import pipeline_kpis
from forecaster import pipeline_forecast
from redistributor import pipeline_redistribucion
from lm_explainer import pipeline_narrativas


def main():
    print("=" * 60)
    print("[PIPELINE] Iniciando pipeline diario Baguer S.A.S.")
    print("=" * 60)

    # 1. ETL
    print("\n--- PASO 1: ETL ---")
    pipeline_etl()

    # 2. KPIs
    print("\n--- PASO 2: KPIs ---")
    pipeline_kpis()

    # 3. Predicción de demanda
    print("\n--- PASO 3: Forecast ---")
    pipeline_forecast()

    # 4. Redistribución
    print("\n--- PASO 4: Redistribución ---")
    pipeline_redistribucion()

    # 5. Narrativas ejecutivas
    print("\n--- PASO 5: Narrativas Ejecutivas ---")
    pipeline_narrativas()

    print("\n" + "=" * 60)
    print("[PIPELINE] Pipeline diario finalizado exitosamente.")
    print("=" * 60)


if __name__ == "__main__":
    main()
