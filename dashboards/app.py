"""
app.py
Dashboard analítico interactivo — Baguer S.A.S.

Ejecutar:
    streamlit run dashboards/app.py
"""
import os
import sys
import json
import subprocess
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Rutas
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(BASE_DIR, "..", "data", "processed")
MAIN_PY = os.path.join(BASE_DIR, "..", "main.py")

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de página
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Baguer S.A.S. | Dashboard Analítico",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS personalizado
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fondo general */
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }

    /* Tarjetas KPI */
    .kpi-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border-left: 4px solid #6366F1;
        margin-bottom: 0.5rem;
    }
    .kpi-card.danger  { border-left-color: #EF4444; }
    .kpi-card.warning { border-left-color: #F59E0B; }
    .kpi-card.success { border-left-color: #10B981; }
    .kpi-card.info    { border-left-color: #38BDF8; }
    .kpi-label  { font-size: 0.78rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.2rem; }
    .kpi-value  { font-size: 2rem; font-weight: 700; color: #F1F5F9; line-height: 1; }
    .kpi-sub    { font-size: 0.75rem; color: #64748B; margin-top: 0.3rem; }

    /* Narrativa card */
    .narrativa-card {
        background: #0F172A;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #1E293B;
        line-height: 1.7;
        color: #CBD5E1;
        font-size: 0.95rem;
    }

    /* Sidebar estilo */
    [data-testid="stSidebar"] { background-color: #0F172A; }
    [data-testid="stSidebar"] .stRadio label { color: #CBD5E1 !important; }

    /* Ocultar footer */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Carga de datos (cacheada 5 min)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos():
    def csv(nombre, **kw):
        p = os.path.join(PROCESSED_PATH, nombre)
        return pd.read_csv(p, **kw) if os.path.exists(p) else pd.DataFrame()

    def json_file(nombre):
        p = os.path.join(PROCESSED_PATH, nombre)
        if not os.path.exists(p):
            return {}
        with open(p, encoding="utf-8") as f:
            return json.load(f)

    kpis     = csv("kpis_resultado.csv")
    tiendas  = csv("dim_tienda.csv")
    prods    = csv("dim_producto.csv")
    forecast = csv("forecast_demanda.csv")
    redis    = csv("sugerencias_redistribucion.csv")
    tallas   = csv("tallas_unificar.csv")
    narr     = json_file("narrativas_ejecutivas.json")

    # Enriquecer KPIs con nombre de tienda
    if not kpis.empty and not tiendas.empty:
        kpis = kpis.merge(tiendas[["tienda_id", "nombre_tienda", "clima", "cargue"]], on="tienda_id", how="left")
        kpis["sku"] = kpis["sku"].astype(str)

    return kpis, tiendas, prods, forecast, redis, tallas, narr


def datos_disponibles():
    return os.path.exists(os.path.join(PROCESSED_PATH, "kpis_resultado.csv"))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers visuales
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_THEME = dict(template="plotly_dark")  # solo para llamadas px.*
_BG = dict(paper_bgcolor="#0F172A", plot_bgcolor="#0F172A", font_color="#CBD5E1")

COLOR_QUIEBRE  = "#EF4444"
COLOR_SOBRE    = "#F59E0B"
COLOR_OK       = "#10B981"
COLOR_PRIMARY  = "#6366F1"
COLOR_INFO     = "#38BDF8"


def kpi_card(label, value, sub="", tipo="info"):
    st.markdown(f"""
    <div class="kpi-card {tipo}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


def color_alerta(val):
    if val is True or val == "Quiebre":
        return "color: #EF4444; font-weight:600"
    if val == "Sobrestock":
        return "color: #F59E0B; font-weight:600"
    if val is False or val == "OK":
        return "color: #10B981"
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👔 Baguer S.A.S.")
    st.markdown("---")
    pagina = st.radio(
        "Navegación",
        options=[
            "🏠  Resumen Nacional",
            "🚨  Alertas & KPIs",
            "📈  Forecast de Demanda",
            "🔄  Redistribución",
            "💬  Narrativas Ejecutivas",
            "▶️   Ejecutar Pipeline",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Pipeline diario · Baguer S.A.S.\nSistema Analítico de Inventarios")

# ─────────────────────────────────────────────────────────────────────────────
# Guardia: datos no disponibles
# ─────────────────────────────────────────────────────────────────────────────
if not datos_disponibles() and "Ejecutar" not in pagina:
    st.warning("⚠️  No se encontraron datos procesados. Ejecuta el pipeline primero.")
    st.info("Ve a **▶️ Ejecutar Pipeline** en el menú lateral para generar los datos.")
    st.stop()

kpis, tiendas, prods, forecast, redis, tallas, narr = cargar_datos()


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — RESUMEN NACIONAL
# ═════════════════════════════════════════════════════════════════════════════
if "Resumen" in pagina:
    st.title("🏠 Resumen Ejecutivo Nacional")
    st.caption(f"Datos actualizados desde `data/processed/` · {len(kpis)} registros KPI")

    # ── KPI cards ────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        n_quiebre = int(kpis["alerta_quiebre"].sum())
        kpi_card("Alertas de Quiebre", f"{n_quiebre:,}", "SKU/tallas < 10 días stock", "danger")
    with c2:
        n_sobre = int(kpis["alerta_sobrestock"].sum())
        kpi_card("Alertas de Sobrestock", f"{n_sobre:,}", "SKU/tallas > 90 días stock", "warning")
    with c3:
        rot_prom = kpis["rotacion"].mean()
        kpi_card("Rotación Promedio", f"{rot_prom:.2f}", "Ventas / Inventario promedio", "success")
    with c4:
        n_curva = len(prods[~prods["estado_curva"]]) if not prods.empty else 0
        kpi_card("SKUs Curva Incompleta", f"{n_curva}", "Sin tallas M o L", "info")

    st.markdown("---")

    # ── Alertas de quiebre por tienda ─────────────────────────────────────────
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("🚨 Alertas de Quiebre por Tienda")
        df_q = (
            kpis[kpis["alerta_quiebre"]]
            .groupby("nombre_tienda")
            .size()
            .reset_index(name="alertas")
            .sort_values("alertas", ascending=True)
        )
        if df_q.empty:
            st.success("Sin alertas de quiebre.")
        else:
            fig = px.bar(
                df_q, x="alertas", y="nombre_tienda", orientation="h",
                color="alertas", color_continuous_scale=["#FCA5A5", "#EF4444"],
                labels={"alertas": "N° Alertas", "nombre_tienda": ""},
                **PLOTLY_THEME,
            )
            fig.update_layout(**_BG, coloraxis_showscale=False, height=380, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col_der:
        st.subheader("📊 Rotación Promedio por Tienda")
        df_rot = (
            kpis.groupby("nombre_tienda")["rotacion"]
            .mean()
            .reset_index()
            .sort_values("rotacion", ascending=True)
        )
        fig2 = px.bar(
            df_rot, x="rotacion", y="nombre_tienda", orientation="h",
            color="rotacion", color_continuous_scale=["#6EE7B7", "#059669"],
            labels={"rotacion": "Rotación", "nombre_tienda": ""},
            **PLOTLY_THEME,
        )
        fig2.update_layout(**_BG, coloraxis_showscale=False, height=380, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Scatter días inventario vs rotación ───────────────────────────────────
    st.subheader("🔵 Días de Inventario vs Rotación (por Tienda)")
    df_scatter = kpis.groupby("nombre_tienda").agg(
        dias_inventario=("dias_inventario", "mean"),
        rotacion=("rotacion", "mean"),
        alertas_quiebre=("alerta_quiebre", "sum"),
    ).reset_index()
    fig3 = px.scatter(
        df_scatter, x="dias_inventario", y="rotacion",
        size="alertas_quiebre", size_max=30,
        color="alertas_quiebre",
        color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
        hover_name="nombre_tienda",
        labels={"dias_inventario": "Días de Inventario (prom.)", "rotacion": "Rotación (prom.)", "alertas_quiebre": "Alertas Quiebre"},
        **PLOTLY_THEME,
    )
    fig3.update_layout(**_BG, height=360, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig3, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — ALERTAS & KPIs
# ═════════════════════════════════════════════════════════════════════════════
elif "Alertas" in pagina:
    st.title("🚨 Alertas y KPIs Detallados")

    # ── Filtros ──────────────────────────────────────────────────────────────
    with st.expander("🔧 Filtros", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        tiendas_disp = sorted(kpis["nombre_tienda"].dropna().unique())
        sel_tiendas = f1.multiselect("Tienda", tiendas_disp, default=[])
        sel_skus    = f2.multiselect("SKU", sorted(kpis["sku"].dropna().unique()), default=[])
        sel_tallas  = f3.multiselect("Talla", sorted(kpis["talla"].dropna().unique()), default=[])
        tipo_alerta = f4.selectbox("Tipo de Alerta", ["Todas", "Solo Quiebre", "Solo Sobrestock", "Sin Alertas"])

    df_fil = kpis.copy()
    if sel_tiendas: df_fil = df_fil[df_fil["nombre_tienda"].isin(sel_tiendas)]
    if sel_skus:    df_fil = df_fil[df_fil["sku"].isin(sel_skus)]
    if sel_tallas:  df_fil = df_fil[df_fil["talla"].isin(sel_tallas)]
    if tipo_alerta == "Solo Quiebre":
        df_fil = df_fil[df_fil["alerta_quiebre"]]
    elif tipo_alerta == "Solo Sobrestock":
        df_fil = df_fil[df_fil["alerta_sobrestock"]]
    elif tipo_alerta == "Sin Alertas":
        df_fil = df_fil[~df_fil["alerta_quiebre"] & ~df_fil["alerta_sobrestock"]]

    # Columna de estado de alerta legible
    def clasificar(row):
        if row["alerta_quiebre"]:   return "Quiebre"
        if row["alerta_sobrestock"]: return "Sobrestock"
        return "OK"

    df_fil = df_fil.copy()
    df_fil["estado"] = df_fil.apply(clasificar, axis=1)

    st.caption(f"{len(df_fil)} registros · {df_fil['alerta_quiebre'].sum()} quiebres · {df_fil['alerta_sobrestock'].sum()} sobrestock")

    # ── Tabla ─────────────────────────────────────────────────────────────────
    cols_mostrar = ["nombre_tienda", "sku", "talla", "rotacion", "dias_inventario",
                    "sell_through_pct", "cobertura_dias", "ventas_totales",
                    "inventario_final", "estado"]
    df_show = df_fil[cols_mostrar].rename(columns={
        "nombre_tienda": "Tienda", "sku": "SKU", "talla": "Talla",
        "rotacion": "Rotación", "dias_inventario": "Días Inv.",
        "sell_through_pct": "Sell-Through", "cobertura_dias": "Cobertura",
        "ventas_totales": "Ventas", "inventario_final": "Stock Final",
        "estado": "Estado",
    })
    styled = df_show.style.map(color_alerta, subset=["Estado"]) \
                          .format({"Rotación": "{:.3f}", "Días Inv.": "{:.1f}",
                                   "Sell-Through": "{:.2%}", "Cobertura": "{:.1f}"})
    st.dataframe(styled, use_container_width=True, height=420)

    # ── Heatmap días inventario ────────────────────────────────────────────────
    st.subheader("🗺️ Mapa de Calor — Días de Inventario (Tienda vs Talla)")
    pivot = df_fil.pivot_table(values="dias_inventario", index="nombre_tienda", columns="talla", aggfunc="mean")
    if not pivot.empty:
        fig_hm = px.imshow(
            pivot,
            color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
            aspect="auto",
            labels={"color": "Días Inv."},
            **PLOTLY_THEME,
        )
        fig_hm.update_layout(**_BG, height=420, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_hm, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — FORECAST DE DEMANDA
# ═════════════════════════════════════════════════════════════════════════════
elif "Forecast" in pagina:
    st.title("📈 Forecast de Demanda — 30 Días")

    if forecast.empty:
        st.warning("No se encontró forecast_demanda.csv. Ejecuta el pipeline.")
        st.stop()

    forecast["fecha"] = pd.to_datetime(forecast["fecha"])
    forecast["sku"]   = forecast["sku"].astype(str)

    # Mapa SKU → etiqueta legible: "1001 – Camisa · MarcaA"
    sku_label: dict = {}
    if not prods.empty:
        prods["sku"] = prods["sku"].astype(str)
        for _, row in prods.iterrows():
            sku_label[row["sku"]] = f"{row['sku']} – {row['categoria']} · {row['marca']}"

    def label(sku: str) -> str:
        return sku_label.get(sku, sku)

    # ── Filtros ──────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    # Tienda: mostrar nombre si está disponible
    tiendas_f = sorted(forecast["tienda_id"].unique())
    if not tiendas.empty:
        tid_label = tiendas.set_index("tienda_id")["nombre_tienda"].to_dict()
        tienda_opts = {tid_label.get(t, str(t)): t for t in tiendas_f}
    else:
        tienda_opts = {str(t): t for t in tiendas_f}
    tienda_nombre_sel = c1.selectbox("Tienda", sorted(tienda_opts.keys()))
    tienda_sel = tienda_opts[tienda_nombre_sel]

    # SKU: mostrar "SKU – Categoría · Marca"
    skus_f = sorted(forecast[forecast["tienda_id"] == tienda_sel]["sku"].unique())
    sku_opts = {label(s): s for s in skus_f}
    sku_label_sel = c2.selectbox("Producto (SKU)", sorted(sku_opts.keys()))
    sku_sel = sku_opts[sku_label_sel]

    tallas_f = sorted(
        forecast[(forecast["tienda_id"] == tienda_sel) & (forecast["sku"] == sku_sel)]["talla"].unique()
    )
    talla_sel = c3.selectbox("Talla", tallas_f)

    df_f = forecast[
        (forecast["tienda_id"] == tienda_sel) &
        (forecast["sku"] == sku_sel) &
        (forecast["talla"] == talla_sel)
    ].sort_values("fecha")

    if df_f.empty:
        st.info("No hay datos de forecast para esta combinación.")
    else:
        total_pred = df_f["demanda_pred"].sum()
        prom_diario = df_f["demanda_pred"].mean()
        producto_desc = label(sku_sel)

        col1, col2 = st.columns(2)
        with col1: kpi_card("Demanda Total 30 días", f"{total_pred:.0f}", f"{producto_desc} · Talla {talla_sel}", "info")
        with col2: kpi_card("Demanda Diaria Promedio", f"{prom_diario:.1f}", "unidades/día", "success")

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=df_f["fecha"], y=df_f["demanda_pred"],
            mode="lines+markers",
            name="Demanda Predicha",
            line=dict(color=COLOR_INFO, width=2.5),
            marker=dict(size=5, color=COLOR_INFO),
            fill="tozeroy",
            fillcolor="rgba(56,189,248,0.08)",
        ))
        fig_fc.update_layout(
            template="plotly_dark", **_BG,
            title=dict(text=f"{producto_desc} · Talla {talla_sel} — {tienda_nombre_sel}", font_size=13, font_color="#94A3B8"),
            height=380,
            xaxis_title="Fecha",
            yaxis_title="Unidades",
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_fc, use_container_width=True)

    # ── Demanda total predicha por tienda ─────────────────────────────────────
    st.subheader("📊 Demanda Total Predicha por Tienda (próximos 30 días)")
    df_total = (
        forecast.groupby("tienda_id")["demanda_pred"]
        .sum()
        .reset_index()
        .sort_values("demanda_pred", ascending=True)
    )
    if not tiendas.empty:
        df_total = df_total.merge(tiendas[["tienda_id", "nombre_tienda"]], on="tienda_id", how="left")
        y_col = "nombre_tienda"
    else:
        y_col = "tienda_id"

    fig_tot = px.bar(
        df_total, x="demanda_pred", y=y_col, orientation="h",
        color="demanda_pred", color_continuous_scale=["#818CF8", "#6366F1"],
        labels={"demanda_pred": "Unidades", y_col: ""},
        **PLOTLY_THEME,
    )
    fig_tot.update_layout(**_BG, coloraxis_showscale=False, height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_tot, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — REDISTRIBUCIÓN
# ═════════════════════════════════════════════════════════════════════════════
elif "Redistribución" in pagina:
    st.title("🔄 Sugerencias de Redistribución")

    # ── Tarjetas resumen ──────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        n_tras = len(redis) if not redis.empty else 0
        kpi_card("Traslados Sugeridos", f"{n_tras}", "origen → destino", "info")
    with c2:
        n_tallas = len(tallas) if not tallas.empty else 0
        kpi_card("SKUs Curva Incompleta", f"{n_tallas}", "faltan tallas M o L", "warning")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📦 Traslados Sugeridos")
        if redis.empty:
            st.success("No hay traslados sugeridos. El inventario está bien distribuido.")
        else:
            df_r = redis.copy()
            if not tiendas.empty:
                nombre_map = tiendas.set_index("tienda_id")["nombre_tienda"].to_dict()
                df_r["origen"] = df_r["tienda_origen"].map(nombre_map).fillna(df_r["tienda_origen"].astype(str))
                df_r["destino"] = df_r["tienda_destino"].map(nombre_map).fillna(df_r["tienda_destino"].astype(str))
            else:
                df_r["origen"] = df_r["tienda_origen"].astype(str)
                df_r["destino"] = df_r["tienda_destino"].astype(str)

            st.dataframe(
                df_r[["sku", "talla", "origen", "destino", "cantidad_sugerida",
                       "dias_inventario_origen", "dias_inventario_destino"]]
                .rename(columns={
                    "sku": "SKU", "talla": "Talla", "origen": "Origen",
                    "destino": "Destino", "cantidad_sugerida": "Cantidad",
                    "dias_inventario_origen": "Días Orig.",
                    "dias_inventario_destino": "Días Dest.",
                }),
                use_container_width=True, height=380,
            )

    with col_b:
        st.subheader("📐 SKUs con Curva de Tallas Incompleta")
        if tallas.empty:
            st.success("Todos los SKUs tienen tallas M y L disponibles.")
        else:
            st.dataframe(
                tallas.rename(columns={
                    "sku": "SKU", "marca": "Marca",
                    "categoria": "Categoría", "tallas_disponibles": "Tallas Activas",
                }),
                use_container_width=True, height=380,
            )

    # ── Chart: cantidad sugerida por tienda destino ───────────────────────────
    if not redis.empty:
        st.subheader("📊 Unidades a Recibir por Tienda Destino")
        df_bar = redis.groupby("tienda_destino")["cantidad_sugerida"].sum().reset_index()
        if not tiendas.empty:
            df_bar = df_bar.merge(tiendas[["tienda_id", "nombre_tienda"]], left_on="tienda_destino", right_on="tienda_id", how="left")
            y_col = "nombre_tienda"
        else:
            y_col = "tienda_destino"
        fig_r = px.bar(
            df_bar.sort_values("cantidad_sugerida", ascending=True),
            x="cantidad_sugerida", y=y_col, orientation="h",
            color="cantidad_sugerida", color_continuous_scale=["#FDE68A", "#F59E0B"],
            labels={"cantidad_sugerida": "Unidades", y_col: ""},
            **PLOTLY_THEME,
        )
        fig_r.update_layout(**_BG, coloraxis_showscale=False, height=340, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_r, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — NARRATIVAS EJECUTIVAS
# ═════════════════════════════════════════════════════════════════════════════
elif "Narrativas" in pagina:
    st.title("💬 Narrativas Ejecutivas por Tienda")

    if not narr or "detalle_por_tienda" not in narr:
        st.warning("No se encontró narrativas_ejecutivas.json. Ejecuta el pipeline.")
        st.stop()

    resumen = narr.get("resumen_nacional", {})
    tiendas_narr = narr.get("detalle_por_tienda", {})

    # ── Resumen Nacional ──────────────────────────────────────────────────────
    st.subheader("🌐 Resumen Nacional")
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Alertas Quiebre", f"{resumen.get('total_alertas_quiebre', '—')}", "nacional", "danger")
    with c2: kpi_card("Alertas Sobrestock", f"{resumen.get('total_alertas_sobrestock', '—')}", "nacional", "warning")
    with c3: kpi_card("Traslados Sugeridos", f"{resumen.get('total_traslados_sugeridos', '—')}", "nacional", "info")
    with c4:
        rot = resumen.get("rotacion_nacional_promedio", 0)
        kpi_card("Rotación Nacional", f"{rot:.3f}", "promedio todas las tiendas", "success")

    st.markdown("---")

    # ── Selector + Narrativa ──────────────────────────────────────────────────
    nombres_tiendas = {v["nombre"]: k for k, v in tiendas_narr.items()}
    tienda_sel = st.selectbox("Selecciona una tienda:", sorted(nombres_tiendas.keys()))

    if tienda_sel:
        t_key = nombres_tiendas[tienda_sel]
        t = tiendas_narr[t_key]

        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Rotación", f"{t['rotacion_promedio']:.3f}", "índice rotación", "success")
        with c2: kpi_card("Sell-Through", f"{t['sell_through_promedio_pct']:.1f}%", "del inventario vendido", "info")
        with c3: kpi_card("Días Inv. Prom.", f"{t['dias_inventario_promedio']:.0f}", "cobertura promedio", "info")

        col_n, col_d = st.columns([3, 2])
        with col_n:
            st.markdown(f"**Narrativa Ejecutiva**")
            texto = t.get("narrativa", "Sin narrativa disponible.")
            st.markdown(f'<div class="narrativa-card">{texto}</div>', unsafe_allow_html=True)

        with col_d:
            st.markdown("**Detalle**")
            detalles = {
                "🌡️ Clima": t.get("clima", "—"),
                "🏷️ SKUs analizados": t.get("n_skus", "—"),
                "🚨 Alertas quiebre": t.get("alertas_quiebre", 0),
                "⚠️ Alertas sobrestock": t.get("alertas_sobrestock", 0),
                "📦 Traslados a recibir": t.get("traslados_a_recibir", 0),
                "🚚 Traslados a enviar": t.get("traslados_a_enviar", 0),
            }
            for k, v in detalles.items():
                st.markdown(f"**{k}:** {v}")

    # ── Ranking: tiendas por urgencia ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Ranking de Tiendas por Urgencia")
    ranking = sorted(
        tiendas_narr.values(),
        key=lambda x: (x.get("alertas_quiebre", 0) + x.get("alertas_sobrestock", 0)),
        reverse=True,
    )
    rows = []
    for t in ranking:
        total_alertas = t.get("alertas_quiebre", 0) + t.get("alertas_sobrestock", 0)
        estado = "🔴 Crítica" if total_alertas > 5 else ("🟡 Moderada" if total_alertas > 0 else "🟢 Óptima")
        rows.append({
            "Tienda": t["nombre"],
            "Clima": t.get("clima", "—"),
            "Rotación": t.get("rotacion_promedio", 0),
            "Días Inv.": t.get("dias_inventario_promedio", 0),
            "Alertas Quiebre": t.get("alertas_quiebre", 0),
            "Alertas Sobrestock": t.get("alertas_sobrestock", 0),
            "Estado": estado,
        })
    df_rank = pd.DataFrame(rows)
    st.dataframe(
        df_rank.style.format({"Rotación": "{:.3f}", "Días Inv.": "{:.1f}"}),
        use_container_width=True, height=400,
    )


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 6 — EJECUTAR PIPELINE
# ═════════════════════════════════════════════════════════════════════════════
elif "Ejecutar" in pagina:
    st.title("▶️  Ejecutar Pipeline")
    st.markdown("Lanza el pipeline diario completo: **ETL → KPIs → Forecast → Redistribución → Narrativas**.")

    col_btn, col_gen = st.columns(2)

    with col_btn:
        st.subheader("🔁 Pipeline Completo")
        st.markdown("Procesa los datos de `data/raw/` y genera todos los archivos en `data/processed/`.")
        if st.button("▶️  Ejecutar `main.py`", type="primary", use_container_width=True):
            with st.spinner("Ejecutando pipeline... esto puede tardar 1-2 minutos."):
                result = subprocess.run(
                    [sys.executable, MAIN_PY],
                    capture_output=True, text=True,
                    cwd=os.path.dirname(MAIN_PY),
                )
            if result.returncode == 0:
                st.success("✅ Pipeline ejecutado exitosamente.")
                st.cache_data.clear()
            else:
                st.error("❌ El pipeline terminó con errores.")
            if result.stdout:
                st.subheader("Salida")
                st.code(result.stdout, language="bash")
            if result.stderr:
                st.subheader("Errores / Warnings")
                st.code(result.stderr, language="bash")

    with col_gen:
        st.subheader("🗂️  Generar Datos Sintéticos")
        st.markdown("Crea CSVs de prueba en `data/raw/` si no tienes datos reales.")
        gen_py = os.path.join(BASE_DIR, "..", "src", "generar_datos_sinteticos.py")
        if st.button("🔧  Generar datos sintéticos", use_container_width=True):
            with st.spinner("Generando datos..."):
                result = subprocess.run(
                    [sys.executable, gen_py],
                    capture_output=True, text=True,
                    cwd=os.path.dirname(MAIN_PY),
                )
            if result.returncode == 0:
                st.success("✅ Datos sintéticos generados en data/raw/")
            else:
                st.error("❌ Error al generar datos.")
            if result.stdout:
                st.code(result.stdout, language="bash")
            if result.stderr:
                st.code(result.stderr, language="bash")

    # ── Estado de archivos ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📂 Estado de Archivos")
    archivos = [
        ("data/raw/tiendas.csv",                 "Tiendas raw"),
        ("data/raw/ventas.csv",                  "Ventas raw"),
        ("data/raw/inventario.csv",              "Inventario raw"),
        ("data/raw/catalogo.csv",                "Catálogo raw"),
        ("data/processed/fact_inventario.csv",   "Fact Inventario"),
        ("data/processed/dim_tienda.csv",        "Dim Tienda"),
        ("data/processed/kpis_resultado.csv",    "KPIs"),
        ("data/processed/forecast_demanda.csv",  "Forecast Demanda"),
        ("data/processed/sugerencias_redistribucion.csv", "Redistribución"),
        ("data/processed/narrativas_ejecutivas.json",     "Narrativas"),
    ]
    raiz = os.path.dirname(MAIN_PY)
    filas = []
    for rel, nombre in archivos:
        p = os.path.join(raiz, rel)
        existe = os.path.exists(p)
        size = f"{os.path.getsize(p)/1024:.1f} KB" if existe else "—"
        filas.append({"Archivo": nombre, "Ruta": rel, "Estado": "✅ Existe" if existe else "❌ Falta", "Tamaño": size})
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
