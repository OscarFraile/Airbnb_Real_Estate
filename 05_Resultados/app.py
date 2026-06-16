import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64, os

st.set_page_config(
    page_title="Airbnb Madrid — Análisis de Inversión",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── THEME ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #1C1C24; }
[data-testid="stSidebar"] { background: #14141E; }
[data-testid="stSidebar"] > div { padding-top: 1rem; }
[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { min-width: 280px !important; max-width: 280px !important; }
h1 { color: #FFFFFF; font-size: 2rem !important; }
h2, h3, h4 { color: #DDDDEE; }
p, li, label { color: #AAAABC; }
.kpi-card {
    background: #2A2A38;
    border-radius: 10px;
    padding: 16px 18px;
    text-align: center;
    border: 1px solid #3A3A50;
}
.kpi-val { font-size: 26px; font-weight: 700; color: #FF385C; margin: 0; }
.kpi-lbl { font-size: 11px; color: #888899; margin: 4px 0 0; text-transform: uppercase; letter-spacing: 0.05em; }
.section-title {
    font-size: 12px; font-weight: 600; color: #888899;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;
}
.sidebar-title { font-size: 22px; font-weight: 700; color: #FFFFFF; margin: 8px 0 2px; }
.sidebar-sub { font-size: 12px; color: #888899; margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)

PINK  = "#FF385C"
DARK  = "#1C1C24"
CARD  = "#2A2A38"
MUTED = "#888899"
WHITE = "#FFFFFF"
COLORS = ["#5B8DB8","#E07B54","#6BBF8E","#C97BB2","#E8C55A","#7EC8C8","#B58A6A","#9B7EC8"]

# ── LOGO ──────────────────────────────────────────────────────────────────────
def get_logo_b64():
    logo_path = "airbnb_vertical_lockup_web.webp"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ── DATA ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("05_Resultados/airbnb_all_periodos.csv")
        if "periodo" not in df.columns:
            df["periodo"] = "Dic 2024"
        return df
    except FileNotFoundError:
        pass
    dfs = []
    for periodo, fname in [
        ("Dic 2024", "05_Resultados/airbnb_dic24.csv"),
        ("Mar 2025", "05_Resultados/airbnb_mar25.csv"),
        ("Jun 2025", "05_Resultados/airbnb_jun25.csv"),
    ]:
        try:
            tmp = pd.read_csv(fname)
            tmp["periodo"] = periodo
            dfs.append(tmp)
        except FileNotFoundError:
            pass
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.error("No se encontró el archivo de datos.")
    st.stop()

if "rentable" in df_raw.columns:
    df_raw["rentable_txt"] = df_raw["rentable"].map(
        {True: "Sí", False: "No", "True": "Sí", "False": "No", 1: "Sí", 0: "No"}
    ).fillna("No")
else:
    df_raw["rentable_txt"] = "No"

PERIODOS  = sorted(df_raw["periodo"].unique(), key=lambda x: {"Dic 2024":1,"Mar 2025":2,"Jun 2025":3}.get(x,99))
DISTRITOS = sorted(df_raw["neighbourhood_group"].dropna().unique())

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_b64 = get_logo_b64()
    if logo_b64:
        st.markdown(f'<img src="data:image/webp;base64,{logo_b64}" style="width:120px;margin-bottom:8px;">', unsafe_allow_html=True)
    else:
        st.markdown('<span style="font-size:32px;">🏠</span>', unsafe_allow_html=True)

    st.markdown('<p class="sidebar-title">Airbnb Madrid</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-sub">Análisis de inversión inmobiliaria</p>', unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio("Navegación", ["📊 Mercado","🎯 Criterios","🤖 Modelo","🔍 Buscador"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**Filtros globales**")
    periodos_sel  = st.multiselect("Periodo",  PERIODOS,  default=PERIODOS)
    distritos_sel = st.multiselect("Distrito", DISTRITOS, default=DISTRITOS)

df = df_raw[
    df_raw["periodo"].isin(periodos_sel) &
    df_raw["neighbourhood_group"].isin(distritos_sel)
].copy()

# ── KPI ROW ───────────────────────────────────────────────────────────────────
def kpi_row(d):
    n           = len(d)
    precio      = d["price"].median()             if "price"               in d else 0
    compra      = d["precio_estimado"].median()   if "precio_estimado"     in d else 0
    ocup        = ((365-d["availability_365"])/365*100).median() if "availability_365" in d else 0
    rent        = d["rentabilidad_anual_pct"].median() if "rentabilidad_anual_pct" in d else 0
    cols = st.columns(5)
    for col,(lbl,val) in zip(cols,[
        ("Nº Inmuebles",          f"{n:,.0f}"),
        ("Precio mediano/noche",  f"{precio:,.0f} €"),
        ("Precio compra mediano", f"{compra:,.0f} €"),
        ("Ocupación mediana",     f"{ocup:.0f} %"),
        ("Rentabilidad mediana",  f"{rent:.1f} %"),
    ]):
        col.markdown(f'<div class="kpi-card"><p class="kpi-val">{val}</p><p class="kpi-lbl">{lbl}</p></div>', unsafe_allow_html=True)

PERIODO_ORD = {"Dic 2024":1,"Mar 2025":2,"Jun 2025":3}

def sort_periodo(s):
    return s.map(PERIODO_ORD)

def fig_layout(fig, h=None):
    upd = dict(paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE,
               legend=dict(font=dict(color=WHITE)), margin=dict(l=10,r=10,t=30,b=10))
    if h:
        upd["height"] = h
    fig.update_layout(**upd)
    fig.update_xaxes(gridcolor="#3A3A50", zerolinecolor="#3A3A50")
    fig.update_yaxes(gridcolor="#3A3A50", zerolinecolor="#3A3A50")
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — MERCADO
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Mercado":
    st.markdown("# Análisis del mercado por distrito")
    kpi_row(df)
    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<p class="section-title">Precio compra vs Ingresos anuales</p>', unsafe_allow_html=True)
        sc = df.groupby("neighbourhood_group").agg(
            precio_estimado=("precio_estimado","median"),
            beneficio_neto_anual=("beneficio_neto_anual","median"),
            n=("price","count")).reset_index()
        fig = px.scatter(sc, x="precio_estimado", y="beneficio_neto_anual",
                         color="neighbourhood_group", size="n", hover_name="neighbourhood_group",
                         labels={"precio_estimado":"Precio compra (€)","beneficio_neto_anual":"Beneficio neto (€/año)","neighbourhood_group":"Distrito"},
                         color_discrete_sequence=COLORS)
        fig_layout(fig)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<p class="section-title">Precio mediano/noche por distrito y periodo</p>', unsafe_allow_html=True)
        ld = df.groupby(["periodo","neighbourhood_group"])["price"].median().reset_index()
        ld = ld.sort_values("periodo", key=sort_periodo)
        fig2 = px.line(ld, x="periodo", y="price", color="neighbourhood_group", markers=True,
                       labels={"price":"Precio (€)","periodo":"Periodo","neighbourhood_group":"Distrito"},
                       color_discrete_sequence=COLORS)
        fig_layout(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="section-title">Precio compra mediano por distrito y periodo</p>', unsafe_allow_html=True)
    ld2 = df.groupby(["periodo","neighbourhood_group"])["precio_estimado"].median().reset_index()
    ld2 = ld2.sort_values("periodo", key=sort_periodo)
    fig3 = px.line(ld2, x="periodo", y="precio_estimado", color="neighbourhood_group", markers=True,
                   labels={"precio_estimado":"Precio compra (€)","periodo":"Periodo","neighbourhood_group":"Distrito"},
                   color_discrete_sequence=COLORS)
    fig_layout(fig3)
    st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CRITERIOS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Criterios":
    st.markdown("# Criterios de selección")
    kpi_row(df)
    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<p class="section-title">Camas vs Precio mediano/noche</p>', unsafe_allow_html=True)
        bd = df[df["beds"].between(1,6)].groupby("beds")["price"].median().reset_index()
        fig = px.line(bd, x="beds", y="price", markers=True,
                      labels={"beds":"Nº camas","price":"Precio (€)"},
                      color_discrete_sequence=[PINK])
        fig_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<p class="section-title">Huéspedes vs Precio y Ocupación</p>', unsafe_allow_html=True)
        ad = (df[df["accommodates"].between(1,10)]
              .assign(ocupacion=lambda d:(365-d["availability_365"])/365*100)
              .groupby("accommodates")
              .agg(price=("price","median"), ocupacion=("ocupacion","median"))
              .reset_index())
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=ad["accommodates"], y=ad["price"],
                                  mode="lines+markers", name="Precio (€)",
                                  line=dict(color=PINK)))
        fig2.add_trace(go.Scatter(x=ad["accommodates"], y=ad["ocupacion"],
                                  mode="lines+markers", name="Ocupación (%)",
                                  line=dict(color="#5B8DB8"), yaxis="y2"))
        fig2.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE,
            xaxis=dict(title="Nº huéspedes", gridcolor="#3A3A50"),
            yaxis=dict(title="Precio (€)", titlefont=dict(color=PINK), gridcolor="#3A3A50"),
            yaxis2=dict(title="Ocupación (%)", titlefont=dict(color="#5B8DB8"),
                        overlaying="y", side="right"),
            legend=dict(font=dict(color=WHITE)),
            margin=dict(l=10,r=10,t=30,b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with c3:
        st.markdown('<p class="section-title">Habitaciones vs Precio y Precio compra</p>', unsafe_allow_html=True)
        hd = (df[df["bedrooms"].between(0,5)]
              .groupby("bedrooms")
              .agg(price=("price","median"), precio_estimado=("precio_estimado","median"))
              .reset_index())
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=hd["bedrooms"], y=hd["price"],
                                  mode="lines+markers", name="Precio alquiler (€)",
                                  line=dict(color=PINK)))
        fig3.add_trace(go.Scatter(x=hd["bedrooms"], y=hd["precio_estimado"],
                                  mode="lines+markers", name="Precio compra (€)",
                                  line=dict(color="#5B8DB8"), yaxis="y2"))
        fig3.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE,
            xaxis=dict(title="Nº habitaciones", gridcolor="#3A3A50"),
            yaxis=dict(title="Precio alquiler (€)", titlefont=dict(color=PINK), gridcolor="#3A3A50"),
            yaxis2=dict(title="Precio compra (€)", titlefont=dict(color="#5B8DB8"),
                        overlaying="y", side="right"),
            legend=dict(font=dict(color=WHITE)),
            margin=dict(l=10,r=10,t=30,b=10),
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<p class="section-title">Nº Reviews vs Precio mediano/noche por distrito</p>', unsafe_allow_html=True)
    rd = (df[df["number_of_reviews"].between(0,200)]
          .groupby(["number_of_reviews","neighbourhood_group"])["price"]
          .median().reset_index())
    fig4 = px.scatter(rd, x="number_of_reviews", y="price", color="neighbourhood_group", opacity=0.6,
                      labels={"number_of_reviews":"Nº Reviews","price":"Precio (€)","neighbourhood_group":"Distrito"},
                      color_discrete_sequence=COLORS)
    fig_layout(fig4)
    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — MODELO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 Modelo":
    st.markdown("# Modelo predictivo")
    st.markdown("---")

    periodos_kpi = ["Dic 2024","Mar 2025","Jun 2025"]
    cols = st.columns(3)
    for col, p in zip(cols, periodos_kpi):
        subset = df_raw[df_raw["periodo"] == p]
        if len(subset) > 0:
            pct = (subset["rentable_txt"] == "Sí").mean() * 100
            col.markdown(f'<div class="kpi-card"><p class="kpi-val">{pct:.1f} %</p><p class="kpi-lbl">Rentables {p}</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<p class="section-title">Evolución % rentables y rentabilidad mediana</p>', unsafe_allow_html=True)
        evol = []
        for p in periodos_kpi:
            subset = df_raw[df_raw["periodo"] == p]
            if len(subset) > 0:
                evol.append({
                    "periodo": p,
                    "pct_rentables": (subset["rentable_txt"] == "Sí").mean() * 100,
                    "rentabilidad":  subset["rentabilidad_anual_pct"].median() if "rentabilidad_anual_pct" in subset else 0,
                })
        evol_df = pd.DataFrame(evol)
        if not evol_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=evol_df["periodo"], y=evol_df["pct_rentables"],
                mode="lines+markers+text", name="% Rentables",
                line=dict(color=PINK, width=2),
                text=evol_df["pct_rentables"].round(1).astype(str)+"%",
                textposition="top center"))
            fig.add_trace(go.Scatter(
                x=evol_df["periodo"], y=evol_df["rentabilidad"],
                mode="lines+markers+text", name="Rentabilidad (%)",
                line=dict(color="#5B8DB8", width=2),
                text=evol_df["rentabilidad"].round(1).astype(str)+"%",
                textposition="bottom center", yaxis="y2"))
            fig.update_layout(
                paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE,
                xaxis=dict(gridcolor="#3A3A50"),
                yaxis=dict(title="% Rentables", titlefont=dict(color=PINK), gridcolor="#3A3A50"),
                yaxis2=dict(title="Rentabilidad (%)", titlefont=dict(color="#5B8DB8"),
                            overlaying="y", side="right"),
                legend=dict(font=dict(color=WHITE)),
                margin=dict(l=10,r=10,t=30,b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<p class="section-title">Top 6 distritos por rentabilidad</p>', unsafe_allow_html=True)
        top6_names = (df.groupby("neighbourhood_group")["rentabilidad_anual_pct"]
                      .median().nlargest(6).index.tolist())
        t6 = (df[df["neighbourhood_group"].isin(top6_names)]
              .groupby(["neighbourhood_group","periodo"])["rentabilidad_anual_pct"]
              .median().reset_index())
        t6 = t6.sort_values("periodo", key=sort_periodo)
        fig2 = px.line(t6, x="periodo", y="rentabilidad_anual_pct",
                       color="neighbourhood_group", markers=True,
                       labels={"rentabilidad_anual_pct":"Rentabilidad (%)","periodo":"Periodo","neighbourhood_group":"Distrito"},
                       color_discrete_sequence=COLORS)
        fig_layout(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="section-title">Beneficio neto anual mediano por periodo — Top 6</p>', unsafe_allow_html=True)
    top6b = (df.groupby("neighbourhood_group")["beneficio_neto_anual"]
             .median().nlargest(6).index.tolist())
    bd = (df[df["neighbourhood_group"].isin(top6b)]
          .groupby(["neighbourhood_group","periodo"])["beneficio_neto_anual"]
          .median().reset_index())
    bd = bd.sort_values("periodo", key=sort_periodo)
    fig3 = px.bar(bd, x="periodo", y="beneficio_neto_anual",
                  color="neighbourhood_group", barmode="group",
                  labels={"beneficio_neto_anual":"Beneficio neto (€)","periodo":"Periodo","neighbourhood_group":"Distrito"},
                  color_discrete_sequence=COLORS)
    fig_layout(fig3)
    st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — BUSCADOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Buscador":
    st.markdown("# Buscador de inmuebles")
    st.markdown("---")

    with st.expander("⚙️ Filtros avanzados", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            rentable_fil = st.selectbox("Rentable", ["Todos","Sí","No"])
            room_types = ["Todos"] + sorted(df["room_type"].dropna().unique().tolist())
            room_fil   = st.selectbox("Tipo alojamiento", room_types)
        with col2:
            precio_max        = st.slider("Precio/noche máx. (€)", 20, 500, 300)
            precio_compra_max = st.slider("Precio compra máx. (€)", 50000, 800000, 400000, step=10000)
        with col3:
            hab_min,  hab_max  = st.slider("Nº Habitaciones", 0, 10, (0,5))
            huesp_min, huesp_max = st.slider("Nº Huéspedes", 1, 16, (1,8))
        with col4:
            reviews_min  = st.slider("Valoración mínima", 0.0, 5.0, 3.0, step=0.1)
            elevador_fil = st.selectbox("Ascensor", ["Todos","Sí","No"])

    mask = (
        (df["price"] <= precio_max) &
        (df["bedrooms"].between(hab_min, hab_max)) &
        (df["accommodates"].between(huesp_min, huesp_max)) &
        (df["precio_estimado"] <= precio_compra_max)
    )
    if "review_scores_rating" in df.columns:
        mask &= df["review_scores_rating"].fillna(0) >= reviews_min
    if rentable_fil != "Todos":
        mask &= df["rentable_txt"] == rentable_fil
    if room_fil != "Todos":
        mask &= df["room_type"] == room_fil
    if elevador_fil != "Todos" and "elevator" in df.columns:
        mask &= df["elevator"] == (1 if elevador_fil == "Sí" else 0)

    df_fil = df[mask]
    kpi_row(df_fil)
    st.markdown(f"**{len(df_fil):,} inmuebles encontrados**")
    st.markdown("---")

    col1, col2 = st.columns([2,1])

    with col1:
        st.markdown('<p class="section-title">Mapa de inmuebles</p>', unsafe_allow_html=True)
        if len(df_fil) > 0 and "latitude" in df_fil.columns:
            map_data = df_fil[["latitude","longitude","neighbourhood_group","price",
                                "precio_estimado","beneficio_neto_anual",
                                "rentabilidad_anual_pct","rentable_txt"]].dropna(
                subset=["latitude","longitude"]).head(5000)
            fig_map = px.scatter_mapbox(
                map_data, lat="latitude", lon="longitude",
                color="rentable_txt",
                color_discrete_map={"Sí":"#6BBF8E","No":"#E07B54"},
                size="rentabilidad_anual_pct", size_max=12,
                hover_name="neighbourhood_group",
                hover_data={"price":True,"precio_estimado":True,
                            "beneficio_neto_anual":True,"rentabilidad_anual_pct":True,
                            "latitude":False,"longitude":False},
                zoom=11, center={"lat":40.4168,"lon":-3.7038},
                mapbox_style="open-street-map",
                labels={"rentable_txt":"Rentable","price":"Precio/noche (€)",
                        "precio_estimado":"Precio compra (€)",
                        "beneficio_neto_anual":"Beneficio neto (€/año)",
                        "rentabilidad_anual_pct":"Rentabilidad (%)"},
            )
            fig_map.update_layout(
                paper_bgcolor=DARK,
                margin=dict(l=0,r=0,t=0,b=0),
                height=450,
                legend=dict(font=dict(color="#333333")),
            )
            st.plotly_chart(fig_map, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">Rentabilidad por distrito</p>', unsafe_allow_html=True)
        if len(df_fil) > 0:
            td = (df_fil.groupby("neighbourhood_group")
                  .agg(n=("price","count"), rentabilidad=("rentabilidad_anual_pct","median"))
                  .reset_index())
            fig_tree = px.treemap(
                td, path=["neighbourhood_group"], values="n",
                color="rentabilidad",
                color_continuous_scale=["#2A2A38","#5B8DB8","#FF385C"],
                hover_data={"rentabilidad":":.1f"},
                labels={"neighbourhood_group":"Distrito","n":"Inmuebles","rentabilidad":"Rentabilidad (%)"},
            )
            fig_tree.update_layout(
                paper_bgcolor=CARD, margin=dict(l=0,r=0,t=0,b=0), height=220, font_color=WHITE)
            st.plotly_chart(fig_tree, use_container_width=True)

        st.markdown('<p class="section-title">Resumen de la selección</p>', unsafe_allow_html=True)
        if len(df_fil) > 0:
            for k, v in {
                "Precio/noche mediano":  f"{df_fil['price'].median():,.0f} €",
                "Precio compra mediano": f"{df_fil['precio_estimado'].median():,.0f} €",
                "Beneficio neto mediano":f"{df_fil['beneficio_neto_anual'].median():,.0f} €/año",
                "Rentabilidad mediana":  f"{df_fil['rentabilidad_anual_pct'].median():.1f} %",
                "% Rentables":           f"{(df_fil['rentable_txt']=='Sí').mean()*100:.1f} %",
            }.items():
                st.markdown(f"**{k}:** {v}")
