"""
lm_explainer.py
Genera narrativas ejecutivas y prioriza alertas usando plantillas basadas en reglas.
No requiere LLM externo; produce texto estructurado listo para usarse en dashboards.

Salida en data/processed/:
  - narrativas_ejecutivas.json : resumen nacional + narrativa por tienda ordenada por prioridad
"""
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed')


def datos_a_json(kpis: pd.DataFrame, sugerencias: pd.DataFrame, tiendas: pd.DataFrame) -> dict:
    """
    Construye un diccionario con el resumen analítico por tienda.
    """
    resultado = {}
    for tienda_id, grp in kpis.groupby('tienda_id'):
        fila_tienda = tiendas[tiendas['tienda_id'] == tienda_id]
        nombre = fila_tienda['nombre_tienda'].values[0] if not fila_tienda.empty else f"Tienda_{tienda_id}"
        clima = fila_tienda['clima'].values[0] if not fila_tienda.empty else 'N/A'

        n_quiebre = int(grp['alerta_quiebre'].sum())
        n_sobre = int(grp['alerta_sobrestock'].sum())
        rotacion_prom = round(float(grp['rotacion'].mean()), 3)
        sell_through_prom = round(float(grp['sell_through_pct'].mean()) * 100, 1)
        dias_inv_prom = round(float(grp['dias_inventario'].mean()), 1)

        traslados_dest = len(sugerencias[sugerencias['tienda_destino'] == tienda_id]) if not sugerencias.empty else 0
        traslados_orig = len(sugerencias[sugerencias['tienda_origen'] == tienda_id]) if not sugerencias.empty else 0

        resultado[str(tienda_id)] = {
            'tienda_id': int(tienda_id),
            'nombre': nombre,
            'clima': clima,
            'n_skus': len(grp),
            'alertas_quiebre': n_quiebre,
            'alertas_sobrestock': n_sobre,
            'rotacion_promedio': rotacion_prom,
            'sell_through_promedio_pct': sell_through_prom,
            'dias_inventario_promedio': dias_inv_prom,
            'traslados_a_recibir': traslados_dest,
            'traslados_a_enviar': traslados_orig,
        }
    return resultado


def generar_narrativa(datos_tienda: dict) -> str:
    """
    Genera una narrativa ejecutiva en texto para una tienda.
    """
    n = datos_tienda['nombre']
    rot = datos_tienda['rotacion_promedio']
    st = datos_tienda['sell_through_promedio_pct']
    dias_inv = datos_tienda['dias_inventario_promedio']
    quiebre = datos_tienda['alertas_quiebre']
    sobre = datos_tienda['alertas_sobrestock']
    recibe = datos_tienda['traslados_a_recibir']
    envia = datos_tienda['traslados_a_enviar']

    partes = [f"{n}: rotación {rot:.3f}, sell-through {st:.1f}%, cobertura promedio {dias_inv:.0f} días."]

    if quiebre > 0:
        partes.append(f"ALERTA: {quiebre} SKU(s) en riesgo de quiebre de stock (< 10 días).")
    if sobre > 0:
        partes.append(f"SOBRESTOCK: {sobre} SKU(s) con más de 90 días de inventario.")
    if recibe > 0:
        partes.append(f"Acción: recibirá {recibe} traslado(s) para cubrir demanda.")
    if envia > 0:
        partes.append(f"Acción: enviará {envia} traslado(s) para liberar inventario excedente.")
    if quiebre == 0 and sobre == 0:
        partes.append("Inventario en niveles óptimos. Sin acciones requeridas.")

    return " ".join(partes)


def priorizar_alertas(datos_json: dict) -> list:
    """
    Ordena las tiendas por prioridad descendente:
      1. Más alertas de quiebre
      2. Más alertas de sobrestock
      3. Menor sell-through
    """
    tiendas_lista = list(datos_json.values())
    tiendas_lista.sort(
        key=lambda t: (
            -t['alertas_quiebre'],
            -t['alertas_sobrestock'],
            t['sell_through_promedio_pct'],
        )
    )
    return tiendas_lista


def pipeline_narrativas():
    """
    Carga KPIs y sugerencias, genera narrativas por tienda y guarda el JSON ejecutivo.
    """
    print("[LM] Iniciando pipeline de narrativas...")

    try:
        kpis = pd.read_csv(os.path.join(PROCESSED_PATH, 'kpis_resultado.csv'))
        tiendas = pd.read_csv(os.path.join(PROCESSED_PATH, 'dim_tienda.csv'))
    except Exception as e:
        print(f"[LM][ERROR] No se pudo leer archivos de KPIs/tiendas: {e}")
        return

    try:
        sugerencias = pd.read_csv(os.path.join(PROCESSED_PATH, 'sugerencias_redistribucion.csv'))
    except FileNotFoundError:
        sugerencias = pd.DataFrame(columns=['tienda_origen', 'tienda_destino'])

    datos = datos_a_json(kpis, sugerencias, tiendas)

    # Agregar narrativa a cada tienda
    for tid in datos:
        datos[tid]['narrativa'] = generar_narrativa(datos[tid])

    # Ordenar por prioridad de atención
    tiendas_priorizadas = priorizar_alertas(datos)

    resultado_final = {
        'fecha_generacion': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
        'total_tiendas': len(datos),
        'resumen_nacional': {
            'total_alertas_quiebre': sum(d['alertas_quiebre'] for d in datos.values()),
            'total_alertas_sobrestock': sum(d['alertas_sobrestock'] for d in datos.values()),
            'total_traslados_sugeridos': sum(d['traslados_a_recibir'] for d in datos.values()),
            'rotacion_nacional_promedio': round(
                sum(d['rotacion_promedio'] for d in datos.values()) / max(len(datos), 1), 3
            ),
        },
        'tiendas_priorizadas': tiendas_priorizadas,
        'detalle_por_tienda': datos,
    }

    ruta = os.path.join(PROCESSED_PATH, 'narrativas_ejecutivas.json')
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(resultado_final, f, ensure_ascii=False, indent=2)

    resumen = resultado_final['resumen_nacional']
    print(f"[LM] narrativas_ejecutivas.json generado para {len(datos)} tiendas.")
    print(f"[LM] Resumen nacional: {resumen}")
    print("[LM] Pipeline de narrativas finalizado.")


if __name__ == "__main__":
    pipeline_narrativas()
