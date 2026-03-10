"""
generar_datos_sinteticos.py
Script para crear archivos CSV sintéticos para pruebas del pipeline Baguer S.A.S.
"""
import os
import random
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(BASE_DIR, '..', 'data', 'raw')
os.makedirs(RAW_PATH, exist_ok=True)

# Parámetros
N_TIENDAS = 15
N_SKUS = 40
TALLAS = ['S', 'M', 'L', 'XL', 'XXL']
N_DIAS = 365
FECHA_INICIO = datetime.now() - timedelta(days=N_DIAS)

# 1. Tiendas
climas = ['Cálido', 'Templado', 'Frío']
cargues = ['Alto', 'Medio', 'Bajo']
tiendas = []
for i in range(1, N_TIENDAS+1):
    tiendas.append({
        'tienda_id': i,
        'nombre_tienda': f'Tienda_{i}',
        'ciudad': f'Ciudad_{random.randint(1,8)}',
        'clima': random.choice(climas),
        'cargue': random.choice(cargues)
    })
pd.DataFrame(tiendas).to_csv(os.path.join(RAW_PATH, 'tiendas.csv'), index=False)

# 2. Catálogo
marcas = ['MarcaA', 'MarcaB', 'MarcaC']
categorias = ['Camisa', 'Pantalón', 'Chaqueta']
catalogo = []
for sku in range(1001, 1001+N_SKUS):
    tallas_disp = random.sample(TALLAS, random.randint(3, len(TALLAS)))
    catalogo.append({
        'sku': sku,
        'marca': random.choice(marcas),
        'categoria': random.choice(categorias),
        'descripcion': f'Producto_{sku}',
        'tallas_disponibles': '|'.join(tallas_disp)
    })
pd.DataFrame(catalogo).to_csv(os.path.join(RAW_PATH, 'catalogo.csv'), index=False)

# 3. Ventas e Inventario
# Perfiles de rotación asignados por combinación tienda/sku/talla:
#   sobrestock (~20%): ventas bajas + stock alto  → dias_inventario > 90
#   quiebre    (~30%): ventas altas + stock bajo  → dias_inventario < 10
#   normal     (~50%): equilibrado               → 10–90 días

PERFILES = {
    # sobrestock: rotación lenta, stock alto → dias_inventario 120-280 días
    # sell-through mensual bajo (~15-25%): mucho stock relativo a ventas
    'sobrestock': {'venta_base': 0.7, 'venta_std': 0.4, 'stock_inicial': (100, 150)},
    # quiebre: demanda media-alta, stock mínimo → dias_inventario 1-9 días
    # sell-through mensual = 100% (siempre se agota)
    'quiebre':    {'venta_base': 2.5, 'venta_std': 0.8, 'stock_inicial': (3, 10)},
    # normal: equilibrado → dias_inventario 20-60 días
    # sell-through mensual realista (~55-75%)
    'normal':     {'venta_base': 1.5, 'venta_std': 0.6, 'stock_inicial': (55, 85)},
}
PESOS_PERFIL = ['sobrestock'] * 20 + ['quiebre'] * 30 + ['normal'] * 50  # 100 fichas

# Pre-asignar perfil a cada combinación única
perfil_map = {}
for tienda in tiendas:
    for prod in catalogo:
        for talla in prod['tallas_disponibles'].split('|'):
            perfil_map[(tienda['tienda_id'], prod['sku'], talla)] = random.choice(PESOS_PERFIL)

ventas = []
inventario = []
for d in range(N_DIAS):
    fecha = (FECHA_INICIO + timedelta(days=d)).strftime('%Y-%m-%d')
    for tienda in tiendas:
        for prod in catalogo:
            for talla in prod['tallas_disponibles'].split('|'):
                perfil = perfil_map[(tienda['tienda_id'], prod['sku'], talla)]
                cfg = PERFILES[perfil]

                # Ventas según perfil
                vta = max(0, int(random.gauss(cfg['venta_base'], cfg['venta_std'])))
                ventas.append({
                    'fecha': fecha,
                    'tienda_id': tienda['tienda_id'],
                    'sku': prod['sku'],
                    'talla': talla,
                    'cantidad_vendida': vta
                })

                # Inventario: día 0 = stock inicial según perfil; resto = varía alrededor del mismo nivel
                lo, hi = cfg['stock_inicial']
                if d == 0:
                    cantidad_stock = random.randint(lo, hi)
                else:
                    # El stock oscila en el rango del perfil independientemente (snapshot diario)
                    cantidad_stock = max(0, random.randint(lo, hi) - vta)
                inventario.append({
                    'fecha': fecha,
                    'tienda_id': tienda['tienda_id'],
                    'sku': prod['sku'],
                    'talla': talla,
                    'cantidad_stock': cantidad_stock
                })

pd.DataFrame(ventas).to_csv(os.path.join(RAW_PATH, 'ventas.csv'), index=False)
pd.DataFrame(inventario).to_csv(os.path.join(RAW_PATH, 'inventario.csv'), index=False)

print('Datos sintéticos generados en data/raw/')
