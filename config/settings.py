# CONFIG_SIMULACION: Diccionario de configuración de umbrales y reglas de negocio para Baguer S.A.S.

CONFIG_SIMULACION = {
    'PERMANENCIA_MINIMA_DIAS': 30,
    'QUIEBRE_STOCK_DIAS': 10,
    'SOBRESTOCK_DIAS': 90,
    'UNIFICACION_TALLAS_ESTADO_CURVA': False,  # Se activa si faltan tallas centrales
    'FACTORES_CRITICOS': {
        'CLIMA': ['Cálido', 'Templado', 'Frío'],
        'CARGUE': None  # Definir según datos de tienda
    }
}
