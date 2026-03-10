PROYECTO_BAGUER/
│
├── config/
│   └── settings.py          # Diccionario CONFIG_SIMULACION (umbrales no hardcodeados).
│
├── data/                    # Capa de Datos [cite: 39]
│   ├── raw/                 # CSVs/JSONs originales (Ventas, Inventario, Tiendas)[cite: 40, 41, 44].
│   └── processed/           # Base analítica (PostgreSQL/SQL Server)[cite: 56].
│
├── src/                     # Capa Analítica (Python) [cite: 45]
│   ├── etl.py               # Limpieza y normalización de datos[cite: 47, 70].
│   ├── kpi_engine.py        # Cálculo de Rotación, Días Inv, Permanencia[cite: 48, 78].
│   ├── forecaster.py        # Modelos Random Forest/XGBoost para demanda[cite: 50, 92].
│   ├── redistributor.py     # Motor de reglas y unificación de tallas[cite: 52, 103].
│   └── lm_explainer.py      # Integración con el modelo de lenguaje (JSON to Narrative)[cite: 53, 124].
│
├── dashboards/              # Capa de Visualización [cite: 58]
│   └── baguer_executive.pbix # Archivo de Power BI[cite: 59, 151].
│
└── main.py                  # Orquestador del pipeline diario[cite: 168].