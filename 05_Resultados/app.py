import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Airbnb Madrid — Análisis de Inversión",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── THEME ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #12121F; }
[data-testid="stSidebar"] { background: #1A1A2E; }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, h4 { color: #FFFFFF; }
p, li, label { color: #CCCCDD; }
.kpi-card {
    background: #252540;
    border-radius: 10px;
    padding: 18px 20px;
    text-align: center;
}
.kpi-val { font-size: 28px; font-weight: 700; color: #FF385C; margin: 0; }
.kpi-lbl { font-size: 12px; color: #9999AA; margin: 4px 0 0; }
.section-title {
    font-size: 14px;
    font-weight: 600;
    color: #9999AA;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

PINK   = "#FF385C"
DARK   = "#12121F"
CARD   = "#252540"
MUTED  = "#9999AA"
WHITE  = "#FFFFFF"

COLORS = px.colors.qualitative.Set2

# ── DATA ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    dfs = []
    files = {
        "Dic 2024": "airbnb_all_periodos.csv",
    }
    try:
        df = pd.read_csv("05_Resultados/airbnb_all_periodos.csv")
        if "periodo" not in df.columns:
            df["periodo"] = "Dic 2024"
        return df
    except FileNotFoundError:
        pass

    for periodo, fname in [
        ("Dic 2024", "airbnb_dic24.csv"),
        ("Mar 2025", "airbnb_mar25.csv"),
        ("Jun 2025", "airbnb_jun25.csv"),
    ]:
        try:
            tmp = pd.read_csv(fname)
            tmp["periodo"] = periodo
            tmp["orden_periodo"] = {"Dic 2024": 1, "Mar 2025": 2, "Jun 2025": 3}[periodo]
            dfs.append(tmp)
        except FileNotFoundError:
            pass

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.error("No se encontró el archivo de datos. Asegúrate de que `airbnb_all_periodos.csv` está en el mismo directorio.")
    st.stop()

# Normalize rentable
if "rentable" in df_raw.columns:
    df_raw["rentable_txt"] = df_raw["rentable"].map(
        {True: "Sí", False: "No", "True": "Sí", "False": "No", 1: "Sí", 0: "No"}
    ).fillna("No")
else:
    df_raw["rentable_txt"] = "No"

PERIODOS = sorted(df_raw["periodo"].unique(), key=lambda x: {"Dic 2024": 1, "Mar 2025": 2, "Jun 2025": 3}.get(x, 99))
DISTRITOS = sorted(df_raw["neighbourhood_group"].dropna().unique())

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏠 Airbnb Madrid")
    st.markdown("**Análisis de inversión inmobiliaria**")
    st.markdown("---")

    page = st.radio(
        "Navegación",
        ["📊 Mercado", "🎯 Criterios", "🤖 Modelo", "🔍 Buscador"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Filtros globales**")

    periodos_sel = st.multiselect(
        "Periodo", PERIODOS, default=PERIODOS
    )

    distritos_sel = st.multiselect(
        "Distrito", DISTRITOS, default=DISTRITOS
    )

df = df_raw[
    df_raw["periodo"].isin(periodos_sel) &
    df_raw["neighbourhood_group"].isin(distritos_sel)
].copy()

# ── KPI ROW ───────────────────────────────────────────────────────────────────
def kpi_row(df_filtered):
    n_inmuebles = len(df_filtered)
    precio_noche = df_filtered["price"].median() if "price" in df_filtered else 0
    precio_compra = df_filtered["precio_estimado"].median() if "precio_estimado" in df_filtered else 0
    ocupacion = ((365 - df_filtered["availability_365"]) / 365 * 100).median() if "availability_365" in df_filtered else 0
    rentabilidad = df_filtered["rentabilidad_anual_pct"].median() if "rentabilidad_anual_pct" in df_filtered else 0

    cols = st.columns(5)
    data = [
        ("Nº Inmuebles", f"{n_inmuebles:,.0f}"),
        ("Precio mediano/noche", f"{precio_noche:,.0f} €"),
        ("Precio compra mediano", f"{precio_compra:,.0f} €"),
        ("Ocupación mediana", f"{ocupacion:.0f} %"),
        ("% Rentabilidad mediana", f"{rentabilidad:.1f} %"),
    ]
    for col, (lbl, val) in zip(cols, data):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <p class="kpi-val">{val}</p>
                <p class="kpi-lbl">{lbl}</p>
            </div>
            """, unsafe_allow_html=True)

# ── PAGE 1: MERCADO ───────────────────────────────────────────────────────────
if page == "📊 Mercado":
    st.markdown("# Análisis del mercado por distrito")
    kpi_row(df)
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-title">Precio compra vs Ingresos anuales</p>', unsafe_allow_html=True)
        scatter_data = (
            df.groupby("neighbourhood_group")
            .agg(
                precio_estimado=("precio_estimado", "median"),
                beneficio_neto_anual=("beneficio_neto_anual", "median"),
                n=("price", "count"),
            )
            .reset_index()
        )
        fig = px.scatter(
            scatter_data,
            x="precio_estimado",
            y="beneficio_neto_anual",
            color="neighbourhood_group",
            size="n",
            hover_name="neighbourhood_group",
            labels={
                "precio_estimado": "Precio compra mediano (€)",
                "beneficio_neto_anual": "Beneficio neto anual mediano (€)",
                "neighbourhood_group": "Distrito",
            },
            color_discrete_sequence=COLORS,
        )
        fig.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD,
            font_color=WHITE, legend_font_color=WHITE,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">Precio mediano/noche por distrito y periodo</p>', unsafe_allow_html=True)
        line_data = (
            df.groupby(["periodo", "neighbourhood_group"])["price"]
            .median()
            .reset_index()
        )
        line_data = line_data.sort_values("periodo", key=lambda s: s.map({"Dic 2024": 1, "Mar 2025": 2, "Jun 2025": 3}))
        fig2 = px.line(
            line_data,
            x="periodo",
            y="price",
            color="neighbourhood_group",
            markers=True,
            labels={"price": "Precio mediano (€)", "periodo": "Periodo", "neighbourhood_group": "Distrito"},
            color_discrete_sequence=COLORS,
        )
        fig2.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD,
            font_color=WHITE, legend_font_color=WHITE,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="section-title">Precio compra mediano por distrito y periodo</p>', unsafe_allow_html=True)
    line_data2 = (
        df.groupby(["periodo", "neighbourhood_group"])["precio_estimado"]
        .median()
        .reset_index()
    )
    line_data2 = line_data2.sort_values("periodo", key=lambda s: s.map({"Dic 2024": 1, "Mar 2025": 2, "Jun 2025": 3}))
    fig3 = px.line(
        line_data2,
        x="periodo",
        y="precio_estimado",
        color="neighbourhood_group",
        markers=True,
        labels={"precio_estimado": "Precio compra mediano (€)", "periodo": "Periodo", "neighbourhood_group": "Distrito"},
        color_discrete_sequence=COLORS,
    )
    fig3.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font_color=WHITE, legend_font_color=WHITE,
    )
    st.plotly_chart(fig3, use_container_width=True)


# ── PAGE 2: CRITERIOS ─────────────────────────────────────────────────────────
elif page == "🎯 Criterios":
    st.markdown("# Criterios de selección")
    kpi_row(df)
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<p class="section-title">Camas vs Precio mediano/noche</p>', unsafe_allow_html=True)
        beds_data = (
            df[df["beds"].between(1, 6)]
            .groupby("beds")["price"]
            .median()
            .reset_index()
        )
        fig = px.line(
            beds_data, x="beds", y="price", markers=True,
            labels={"beds": "Nº camas", "price": "Precio mediano (€)"},
            color_discrete_sequence=[PINK],
        )
        fig.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">Huéspedes vs Precio y Ocupación</p>', unsafe_allow_html=True)
        acc_data = (
            df[df["accommodates"].between(1, 10)]
            .assign(ocupacion=lambda d: (365 - d["availability_365"]) / 365 * 100)
            .groupby("accommodates")
            .agg(price=("price", "median"), ocupacion=("ocupacion", "median"))
            .reset_index()
        )
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=acc_data["accommodates"], y=acc_data["price"],
                                   mode="lines+markers", name="Precio (€)", line=dict(color=PINK)))
        fig2.add_trace(go.Scatter(x=acc_data["accommodates"], y=acc_data["ocupacion"],
                                   mode="lines+markers", name="Ocupación (%)",
                                   line=dict(color="#378ADD"), yaxis="y2"))
        fig2.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE,
            xaxis_title="Nº huéspedes",
            yaxis=dict(title="Precio (€)", titlefont_color=PINK),
            yaxis2=dict(title="Ocupación (%)", titlefont_color="#378ADD",
                        overlaying="y", side="right"),
            legend=dict(font_color=WHITE),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        st.markdown('<p class="section-title">Habitaciones vs Precio y Precio compra</p>', unsafe_allow_html=True)
        bed_data = (
            df[df["bedrooms"].between(0, 5)]
            .groupby("bedrooms")
            .agg(price=("price", "median"), precio_estimado=("precio_estimado", "median"))
            .reset_index()
        )
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=bed_data["bedrooms"], y=bed_data["price"],
                                   mode="lines+markers", name="Precio alquiler (€)", line=dict(color=PINK)))
        fig3.add_trace(go.Scatter(x=bed_data["bedrooms"], y=bed_data["precio_estimado"],
                                   mode="lines+markers", name="Precio compra (€)",
                                   line=dict(color="#378ADD"), yaxis="y2"))
        fig3.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE,
            xaxis_title="Nº habitaciones",
            yaxis=dict(title="Precio alquiler (€)", titlefont_color=PINK),
            yaxis2=dict(title="Precio compra (€)", titlefont_color="#378ADD",
                        overlaying="y", side="right"),
            legend=dict(font_color=WHITE),
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<p class="section-title">Nº Reviews vs Precio mediano/noche por distrito</p>', unsafe_allow_html=True)
    rev_data = (
        df[df["number_of_reviews"].between(0, 200)]
        .groupby(["number_of_reviews", "neighbourhood_group"])["price"]
        .median()
        .reset_index()
    )
    fig4 = px.scatter(
        rev_data, x="number_of_reviews", y="price",
        color="neighbourhood_group",
        labels={"number_of_reviews": "Nº Reviews", "price": "Precio mediano (€)", "neighbourhood_group": "Distrito"},
        color_discrete_sequence=COLORS,
        opacity=0.6,
    )
    fig4.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE, legend_font_color=WHITE)
    st.plotly_chart(fig4, use_container_width=True)


# ── PAGE 3: MODELO ────────────────────────────────────────────────────────────
elif page == "🤖 Modelo":
    st.markdown("# Modelo predictivo")
    st.markdown("---")

    # KPIs por periodo
    periodos_kpi = ["Dic 2024", "Mar 2025", "Jun 2025"]
    cols = st.columns(3)
    for col, p in zip(cols, periodos_kpi):
        subset = df_raw[df_raw["periodo"] == p]
        if len(subset) > 0:
            pct = (subset["rentable_txt"] == "Sí").mean() * 100
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                    <p class="kpi-val">{pct:.1f} %</p>
                    <p class="kpi-lbl">Rentables {p}</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-title">Evolución % rentables y rentabilidad mediana</p>', unsafe_allow_html=True)
        evol = []
        for p in periodos_kpi:
            subset = df_raw[df_raw["periodo"] == p]
            if len(subset) > 0:
                evol.append({
                    "periodo": p,
                    "pct_rentables": (subset["rentable_txt"] == "Sí").mean() * 100,
                    "rentabilidad": subset["rentabilidad_anual_pct"].median(),
                })
        evol_df = pd.DataFrame(evol)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=evol_df["periodo"], y=evol_df["pct_rentables"],
                                  mode="lines+markers+text", name="% Rentables",
                                  line=dict(color=PINK, width=2),
                                  text=evol_df["pct_rentables"].round(1).astype(str) + "%",
                                  textposition="top center"))
        fig.add_trace(go.Scatter(x=evol_df["periodo"], y=evol_df["rentabilidad"],
                                  mode="lines+markers+text", name="Rentabilidad mediana (%)",
                                  line=dict(color="#378ADD", width=2),
                                  text=evol_df["rentabilidad"].round(1).astype(str) + "%",
                                  textposition="bottom center", yaxis="y2"))
        fig.update_layout(
            paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE,
            yaxis=dict(title="% Rentables", titlefont_color=PINK),
            yaxis2=dict(title="Rentabilidad (%)", titlefont_color="#378ADD",
                        overlaying="y", side="right"),
            legend=dict(font_color=WHITE),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">Top 6 distritos por rentabilidad</p>', unsafe_allow_html=True)
        top6_data = (
            df.groupby(["neighbourhood_group", "periodo"])["rentabilidad_anual_pct"]
            .median()
            .reset_index()
        )
        top6_names = (
            df.groupby("neighbourhood_group")["rentabilidad_anual_pct"]
            .median()
            .nlargest(6)
            .index.tolist()
        )
        top6_data = top6_data[top6_data["neighbourhood_group"].isin(top6_names)]
        top6_data = top6_data.sort_values("periodo", key=lambda s: s.map({"Dic 2024": 1, "Mar 2025": 2, "Jun 2025": 3}))
        fig2 = px.line(
            top6_data, x="periodo", y="rentabilidad_anual_pct",
            color="neighbourhood_group", markers=True,
            labels={"rentabilidad_anual_pct": "Rentabilidad mediana (%)", "periodo": "Periodo", "neighbourhood_group": "Distrito"},
            color_discrete_sequence=COLORS,
        )
        fig2.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE, legend_font_color=WHITE)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="section-title">Beneficio neto anual mediano por periodo</p>', unsafe_allow_html=True)
    ben_data = (
        df.groupby(["neighbourhood_group", "periodo"])["beneficio_neto_anual"]
        .median()
        .reset_index()
    )
    top6_ben = (
        df.groupby("neighbourhood_group")["beneficio_neto_anual"]
        .median()
        .nlargest(6)
        .index.tolist()
    )
    ben_data = ben_data[ben_data["neighbourhood_group"].isin(top6_ben)]
    ben_data = ben_data.sort_values("periodo", key=lambda s: s.map({"Dic 2024": 1, "Mar 2025": 2, "Jun 2025": 3}))
    fig3 = px.bar(
        ben_data, x="periodo", y="beneficio_neto_anual",
        color="neighbourhood_group", barmode="group",
        labels={"beneficio_neto_anual": "Beneficio neto mediano (€)", "periodo": "Periodo", "neighbourhood_group": "Distrito"},
        color_discrete_sequence=COLORS,
    )
    fig3.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=WHITE, legend_font_color=WHITE)
    st.plotly_chart(fig3, use_container_width=True)


# ── PAGE 4: BUSCADOR ──────────────────────────────────────────────────────────
elif page == "🔍 Buscador":
    st.markdown("# Buscador de inmuebles")
    st.markdown("---")

    with st.expander("⚙️ Filtros avanzados", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            rentable_fil = st.selectbox("Rentable", ["Todos", "Sí", "No"])
            room_types = ["Todos"] + sorted(df["room_type"].dropna().unique().tolist())
            room_fil = st.selectbox("Tipo alojamiento", room_types)

        with col2:
            precio_max = st.slider("Precio/noche máx. (€)", 20, 500, 300)
            precio_compra_max = st.slider("Precio compra máx. (€)", 50000, 800000, 400000, step=10000)

        with col3:
            hab_min, hab_max = st.slider("Nº Habitaciones", 0, 10, (0, 5))
            huesp_min, huesp_max = st.slider("Nº Huéspedes", 1, 16, (1, 8))

        with col4:
            reviews_min = st.slider("Valoración mínima", 0.0, 5.0, 3.0, step=0.1)
            elevador_fil = st.selectbox("Ascensor", ["Todos", "Sí", "No"])

    # Apply filters
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

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<p class="section-title">Mapa de inmuebles</p>', unsafe_allow_html=True)
        if len(df_fil) > 0 and "latitude" in df_fil.columns:
            map_data = df_fil[["latitude", "longitude", "neighbourhood_group",
                                "price", "precio_estimado", "beneficio_neto_anual",
                                "rentabilidad_anual_pct", "rentable_txt"]].dropna(
                subset=["latitude", "longitude"]
            ).head(5000)

            fig_map = px.scatter_mapbox(
                map_data,
                lat="latitude",
                lon="longitude",
                color="rentable_txt",
                color_discrete_map={"Sí": "#1D9E75", "No": "#E24B4A"},
                size="rentabilidad_anual_pct",
                size_max=12,
                hover_name="neighbourhood_group",
                hover_data={
                    "price": True,
                    "precio_estimado": True,
                    "beneficio_neto_anual": True,
                    "rentabilidad_anual_pct": True,
                    "latitude": False,
                    "longitude": False,
                },
                zoom=11,
                center={"lat": 40.4168, "lon": -3.7038},
                mapbox_style="carto-darkmatter",
                labels={
                    "rentable_txt": "Rentable",
                    "price": "Precio/noche (€)",
                    "precio_estimado": "Precio compra (€)",
                    "beneficio_neto_anual": "Beneficio neto (€/año)",
                    "rentabilidad_anual_pct": "Rentabilidad (%)",
                },
            )
            fig_map.update_layout(
                paper_bgcolor=DARK,
                margin=dict(l=0, r=0, t=0, b=0),
                height=450,
                legend_font_color=WHITE,
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Sin inmuebles con coordenadas para mostrar.")

    with col2:
        st.markdown('<p class="section-title">Rentabilidad por distrito</p>', unsafe_allow_html=True)
        if len(df_fil) > 0:
            treemap_data = (
                df_fil.groupby("neighbourhood_group")
                .agg(n=("price", "count"), rentabilidad=("rentabilidad_anual_pct", "median"))
                .reset_index()
            )
            fig_tree = px.treemap(
                treemap_data,
                path=["neighbourhood_group"],
                values="n",
                color="rentabilidad",
                color_continuous_scale=["#1A1A2E", PINK],
                hover_data={"rentabilidad": ":.1f"},
                labels={"neighbourhood_group": "Distrito", "n": "Inmuebles", "rentabilidad": "Rentabilidad (%)"},
            )
            fig_tree.update_layout(
                paper_bgcolor=CARD,
                margin=dict(l=0, r=0, t=0, b=0),
                height=220,
                font_color=WHITE,
            )
            st.plotly_chart(fig_tree, use_container_width=True)

        st.markdown('<p class="section-title">Resumen de la selección</p>', unsafe_allow_html=True)
        if len(df_fil) > 0:
            metrics = {
                "Precio/noche mediano": f"{df_fil['price'].median():,.0f} €",
                "Precio compra mediano": f"{df_fil['precio_estimado'].median():,.0f} €",
                "Beneficio neto mediano": f"{df_fil['beneficio_neto_anual'].median():,.0f} €/año",
                "Rentabilidad mediana": f"{df_fil['rentabilidad_anual_pct'].median():.1f} %",
                "% Rentables": f"{(df_fil['rentable_txt']=='Sí').mean()*100:.1f} %",
            }
            for k, v in metrics.items():
                st.markdown(f"**{k}:** {v}")
        else:
            st.warning("Sin resultados con los filtros seleccionados.")
