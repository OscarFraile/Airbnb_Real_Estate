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

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #2B2B2B; }
[data-testid="stSidebar"] { background: #1E1E1E; }
[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { min-width: 240px !important; max-width: 240px !important; }
h1 { color: #EEEEEE; font-size: 4rem !important; }
h2, h3, h4 { color: #CCCCCC; }
p, li, label { color: #AAAAAA; }
.kpi-card { background: #3A3A3A; border-radius: 10px; padding: 50px 7px; text-align: center; border: 1px solid #505050; }
.kpi-lbl { font-size: 11px; color: #888888; margin: 0 0 4px 0; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-val { font-size: 38px !important; font-weight: 700; color: #FF385C; margin: 0; line-height: 1.1; }
details > summary { background: #3A3A3A !important; color: #EEEEEE !important; border: 1px solid #505050 !important; border-radius: 8px; }
details { border: none !important; }
.section-title { font-size: 11px; font-weight: 600; color: #888888; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
div[data-baseweb="select"] > div { background-color: #3A3A3A !important; border-color: #505050 !important; }
ul[data-baseweb="menu"] { background-color: #2B2B2B !important; }
li[role="option"] { background-color: #2B2B2B !important; color: #EEEEEE !important; }
li[role="option"]:hover { background-color: #3A3A3A !important; }
[data-testid="stRadio"] label p { font-size: 20px !important; }
[data-testid="stSidebar"] img { display: block; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

PINK   = "#FF385C"
DARK   = "#2B2B2B"
CARD   = "#3A3A3A"
WHITE  = "#EEEEEE"
COLORS = ["#5B8DB8","#E07B54","#6BBF8E","#C97BB2","#E8C55A","#7EC8C8","#B58A6A","#9B7EC8"]

def get_logo_b64():
    for p in ["99_Media/airbnb_vertical_lockup_web.webp","05_Resultados/airbnb_vertical_lockup_web.webp","airbnb_vertical_lockup_web.webp"]:
        if os.path.exists(p):
            with open(p,"rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

@st.cache_data
def load_data():
    for path in ["05_Resultados/airbnb_all_periodos.csv","airbnb_all_periodos.csv"]:
        try:
            df = pd.read_csv(path)
            if "periodo" not in df.columns:
                df["periodo"] = "Dic24"
            return df
        except FileNotFoundError:
            pass
    dfs = []
    for periodo, fname in [("Dic24","05_Resultados/airbnb_dic24.csv"),("Mar25","05_Resultados/airbnb_mar25.csv"),("Jun25","05_Resultados/airbnb_jun25.csv")]:
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

# Normalizar periodo
PERIODO_ORD = {"Dic24":1,"Mar25":2,"Jun25":3,"Dic 2024":1,"Mar 2025":2,"Jun 2025":3}
df_raw["periodo"] = df_raw["periodo"].astype(str).str.strip()

if "rentable" in df_raw.columns:
    df_raw["rentable_txt"] = df_raw["rentable"].map({True:"Sí",False:"No","True":"Sí","False":"No",1:"Sí",0:"No"}).fillna("No")
else:
    df_raw["rentable_txt"] = "No"

PERIODOS  = sorted(df_raw["periodo"].unique(), key=lambda x: PERIODO_ORD.get(x,99))
DISTRITOS = sorted(df_raw["neighbourhood_group"].dropna().unique())

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_b64 = get_logo_b64()
    if logo_b64:
        st.markdown(f'<img src="data:image/webp;base64,{logo_b64}" style="width:130px;margin-bottom:8px;">', unsafe_allow_html=True)
    else:
        st.markdown('<span style="font-size:32px;">🏠</span>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:32px;font-weight:700;color:#EEE;margin:8px 0 2px;text-align:center;">Airbnb Madrid</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:18px;color:#888;margin:8px 0 2px;text-align:center;">Análisis de inversión inmobiliaria</p>', unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navegación",["📊 Mercado","🎯 Criterios","📈 Modelo","🔍 Buscador"],label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Filtros globales**")
    periodos_sel  = st.multiselect("Periodo",  PERIODOS,  default=PERIODOS)
    distritos_sel = st.multiselect("Distrito", DISTRITOS, default=DISTRITOS)

df = df_raw[df_raw["periodo"].isin(periodos_sel) & df_raw["neighbourhood_group"].isin(distritos_sel)].copy()

def kpi_row(d):
    n     = len(d)
    precio = d["price"].median()             if "price"               in d.columns else 0
    compra = d["precio_estimado"].median()   if "precio_estimado"     in d.columns else 0
    ocup   = ((365-d["availability_365"])/365*100).median() if "availability_365" in d.columns else 0
    rent   = d["rentabilidad_anual_pct"].median() if "rentabilidad_anual_pct" in d.columns else 0
    for col,(lbl,val) in zip(st.columns(5),[
        ("Nº Inmuebles",f"{n:,.0f}"),("Precio mediano/noche",f"{precio:,.0f} €"),
        ("Precio compra mediano",f"{compra:,.0f} €"),("Ocupación mediana",f"{ocup:.0f} %"),
        ("Rentabilidad mediana",f"{rent:.1f} %"),
    ]):
        col.markdown(f'<div class="kpi-card"><p class="kpi-lbl">{lbl}</p><p class="kpi-val">{val}</p></div>',unsafe_allow_html=True)

def sort_p(s): return s.map(PERIODO_ORD).fillna(99)

def fl(fig,h=None):
    upd = dict(paper_bgcolor=CARD,plot_bgcolor=CARD,font_color=WHITE,
               legend=dict(font=dict(color=WHITE)),margin=dict(l=10,r=10,t=30,b=10))
    if h: upd["height"]=h
    fig.update_layout(**upd)
    fig.update_xaxes(gridcolor="#505050",zerolinecolor="#505050")
    fig.update_yaxes(gridcolor="#505050",zerolinecolor="#505050")
    return fig

def dual_ax(fig,t1,t2,c1,c2):
    fig.update_layout(
        paper_bgcolor=CARD,plot_bgcolor=CARD,font_color=WHITE,
        xaxis=dict(gridcolor="#505050"),
        yaxis=dict(title=dict(text=t1,font=dict(color=c1)),gridcolor="#505050"),
        yaxis2=dict(title=dict(text=t2,font=dict(color=c2)),overlaying="y",side="right"),
        legend=dict(font=dict(color=WHITE)),
        margin=dict(l=10,r=10,t=30,b=10),
    )

# ══ MERCADO ══════════════════════════════════════════════════════════════════
if page == "📊 Mercado":
    st.markdown("# Análisis por Distrito")
    kpi_row(df)
    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<p class="section-title">Precio compra vs Ingresos anuales</p>',unsafe_allow_html=True)
        sc = df.groupby("neighbourhood_group").agg(precio_estimado=("precio_estimado","median"),beneficio_neto_anual=("beneficio_neto_anual","median"),n=("price","count")).reset_index()
        fig = px.scatter(sc,x="precio_estimado",y="beneficio_neto_anual",color="neighbourhood_group",size="n",hover_name="neighbourhood_group",labels={"precio_estimado":"Precio compra (€)","beneficio_neto_anual":"Beneficio neto (€/año)","neighbourhood_group":"Distrito"},color_discrete_sequence=COLORS)
        fl(fig); fig.update_layout(showlegend=False); st.plotly_chart(fig,use_container_width=True)
    with c2:
        st.markdown('<p class="section-title">Precio mediano/noche por distrito y periodo</p>',unsafe_allow_html=True)
        ld = df.groupby(["periodo","neighbourhood_group"])["price"].median().reset_index().sort_values("periodo",key=sort_p)
        fig2 = px.line(ld,x="periodo",y="price",color="neighbourhood_group",markers=True,labels={"price":"Precio (€)","periodo":"Periodo","neighbourhood_group":"Distrito"},color_discrete_sequence=COLORS)
        fl(fig2); st.plotly_chart(fig2,use_container_width=True)
    st.markdown('<p class="section-title">Precio compra mediano por distrito y periodo</p>',unsafe_allow_html=True)
    ld2 = df.groupby(["periodo","neighbourhood_group"])["precio_estimado"].median().reset_index().sort_values("periodo",key=sort_p)
    fig3 = px.line(ld2,x="periodo",y="precio_estimado",color="neighbourhood_group",markers=True,labels={"precio_estimado":"Precio compra (€)","periodo":"Periodo","neighbourhood_group":"Distrito"},color_discrete_sequence=COLORS)
    fl(fig3); st.plotly_chart(fig3,use_container_width=True)

# ══ CRITERIOS ════════════════════════════════════════════════════════════════
elif page == "🎯 Criterios":
    st.markdown("# Criterios de selección")
    kpi_row(df)
    st.markdown("---")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<p class="section-title">Camas vs Precio mediano/noche</p>',unsafe_allow_html=True)
        bd = df[df["beds"].between(1,6)].groupby("beds")["price"].median().reset_index()
        fig = px.line(bd,x="beds",y="price",markers=True,labels={"beds":"Nº camas","price":"Precio (€)"},color_discrete_sequence=[PINK])
        fl(fig); st.plotly_chart(fig,use_container_width=True)
    with c2:
        st.markdown('<p class="section-title">Huéspedes vs Precio y Ocupación</p>',unsafe_allow_html=True)
        ad = (df[df["accommodates"].between(1,10)].assign(ocupacion=lambda d:(365-d["availability_365"])/365*100).groupby("accommodates").agg(price=("price","median"),ocupacion=("ocupacion","median")).reset_index())
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=ad["accommodates"],y=ad["price"],mode="lines+markers",name="Precio (€)",line=dict(color=PINK)))
        fig2.add_trace(go.Scatter(x=ad["accommodates"],y=ad["ocupacion"],mode="lines+markers",name="Ocupación (%)",line=dict(color="#5B8DB8"),yaxis="y2"))
        dual_ax(fig2,"Precio (€)","Ocupación (%)",PINK,"#5B8DB8"); st.plotly_chart(fig2,use_container_width=True)
    with c3:
        st.markdown('<p class="section-title">Habitaciones vs Precio y Precio compra</p>',unsafe_allow_html=True)
        hd = (df[df["bedrooms"].between(0,5)].groupby("bedrooms").agg(price=("price","median"),precio_estimado=("precio_estimado","median")).reset_index())
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=hd["bedrooms"],y=hd["price"],mode="lines+markers",name="Precio alquiler (€)",line=dict(color=PINK)))
        fig3.add_trace(go.Scatter(x=hd["bedrooms"],y=hd["precio_estimado"],mode="lines+markers",name="Precio compra (€)",line=dict(color="#5B8DB8"),yaxis="y2"))
        dual_ax(fig3,"Precio alquiler (€)","Precio compra (€)",PINK,"#5B8DB8"); st.plotly_chart(fig3,use_container_width=True)
    st.markdown('<p class="section-title">Nº Reviews vs Precio mediano/noche por distrito</p>',unsafe_allow_html=True)
    rd = df[df["number_of_reviews"].between(0,200)].groupby(["number_of_reviews","neighbourhood_group"])["price"].median().reset_index()
    fig4 = px.scatter(rd,x="number_of_reviews",y="price",color="neighbourhood_group",opacity=0.6,labels={"number_of_reviews":"Nº Reviews","price":"Precio (€)","neighbourhood_group":"Distrito"},color_discrete_sequence=COLORS)
    fl(fig4); st.plotly_chart(fig4,use_container_width=True)

# ══ MODELO ════════════════════════════════════════════════════════════════════
elif page == "📈 Modelo":
    st.markdown("# Modelo predictivo")
    st.markdown("---")
    periodos_kpi = PERIODOS
    for col,p in zip(st.columns(min(3,len(periodos_kpi))), periodos_kpi[:3]):
        s = df_raw[df_raw["periodo"]==p]
        if len(s)>0:
            pct = (s["rentable_txt"]=="Sí").mean()*100
            col.markdown(f'<div class="kpi-card"><p class="kpi-lbl">Rentables {p}</p><p class="kpi-val">{pct:.1f} %</p></div>',unsafe_allow_html=True)
    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<p class="section-title">Evolución % rentables y rentabilidad mediana</p>',unsafe_allow_html=True)
        evol = []
        for p in periodos_kpi:
            s = df_raw[df_raw["periodo"]==p]
            if len(s)>0:
                evol.append({"periodo":p,"pct_rentables":(s["rentable_txt"]=="Sí").mean()*100,"rentabilidad":s["rentabilidad_anual_pct"].median() if "rentabilidad_anual_pct" in s.columns else 0})
        if evol:
            evol_df = pd.DataFrame(evol).sort_values("periodo",key=sort_p)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=evol_df["periodo"],y=evol_df["pct_rentables"],mode="lines+markers+text",name="% Rentables",line=dict(color=PINK,width=2),text=evol_df["pct_rentables"].round(1).astype(str)+"%",textposition="top center"))
            fig.add_trace(go.Scatter(x=evol_df["periodo"],y=evol_df["rentabilidad"],mode="lines+markers+text",name="Rentabilidad (%)",line=dict(color="#5B8DB8",width=2),text=evol_df["rentabilidad"].round(1).astype(str)+"%",textposition="bottom center",yaxis="y2"))
            dual_ax(fig,"% Rentables","Rentabilidad (%)",PINK,"#5B8DB8"); st.plotly_chart(fig,use_container_width=True)
        else:
            st.info("Sin datos para los periodos seleccionados.")
    with c2:
        st.markdown('<p class="section-title">Top 6 distritos por rentabilidad</p>',unsafe_allow_html=True)
        if "rentabilidad_anual_pct" in df.columns and len(df)>0:
            top6 = df.groupby("neighbourhood_group")["rentabilidad_anual_pct"].median().nlargest(6).index.tolist()
            t6 = df[df["neighbourhood_group"].isin(top6)].groupby(["neighbourhood_group","periodo"])["rentabilidad_anual_pct"].median().reset_index().sort_values("periodo",key=sort_p)
            fig2 = px.line(t6,x="periodo",y="rentabilidad_anual_pct",color="neighbourhood_group",markers=True,labels={"rentabilidad_anual_pct":"Rentabilidad (%)","periodo":"Periodo","neighbourhood_group":"Distrito"},color_discrete_sequence=COLORS)
            fl(fig2); st.plotly_chart(fig2,use_container_width=True)
    st.markdown('<p class="section-title">Beneficio neto anual mediano — Top 6</p>',unsafe_allow_html=True)
    if "beneficio_neto_anual" in df.columns and len(df)>0:
        top6b = df.groupby("neighbourhood_group")["beneficio_neto_anual"].median().nlargest(6).index.tolist()
        bd = df[df["neighbourhood_group"].isin(top6b)].groupby(["neighbourhood_group","periodo"])["beneficio_neto_anual"].median().reset_index().sort_values("periodo",key=sort_p)
        fig3 = px.bar(bd,x="periodo",y="beneficio_neto_anual",color="neighbourhood_group",barmode="group",labels={"beneficio_neto_anual":"Beneficio neto (€)","periodo":"Periodo","neighbourhood_group":"Distrito"},color_discrete_sequence=COLORS)
        fl(fig3); st.plotly_chart(fig3,use_container_width=True)

# ══ BUSCADOR ══════════════════════════════════════════════════════════════════
elif page == "🔍 Buscador":
    st.markdown("# Buscador de inmuebles")
    st.markdown("---")
    with st.expander("⚙️ Filtros avanzados",expanded=True):
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            rentable_fil = st.selectbox("Rentable",["Todos","Sí","No"])
            room_fil = st.selectbox("Tipo alojamiento",["Todos"]+sorted(df["room_type"].dropna().unique().tolist()))
        with c2:
            precio_min, precio_max = st.slider("Precio/noche (€)",20,500,(20,300))
            precio_compra_min, precio_compra_max = st.slider("Precio compra (€)",50000,800000,(50000,400000),step=10000)
        with c3:
            hab_min,hab_max = st.slider("Nº Habitaciones",0,10,(0,5))
            huesp_min,huesp_max = st.slider("Nº Huéspedes",1,16,(1,8))
        with c4:
            reviews_min, reviews_max = st.slider("Valoración",0.0,5.0,(3.0,5.0),step=0.1)
            elevador_fil = st.selectbox("Ascensor",["Todos","Sí","No"])
    mask = (df["price"].between(precio_min,precio_max))&(df["bedrooms"].between(hab_min,hab_max))&(df["accommodates"].between(huesp_min,huesp_max))&(df["precio_estimado"].between(precio_compra_min,precio_compra_max))
    if "review_scores_rating" in df.columns: mask &= df["review_scores_rating"].fillna(0).between(reviews_min,reviews_max)
    if rentable_fil!="Todos": mask &= df["rentable_txt"]==rentable_fil
    if room_fil!="Todos": mask &= df["room_type"]==room_fil
    if elevador_fil!="Todos" and "elevator" in df.columns: mask &= df["elevator"]==(1 if elevador_fil=="Sí" else 0)
    df_fil = df[mask]
    kpi_row(df_fil)
    st.markdown(f"**{len(df_fil):,} inmuebles encontrados**")
    st.markdown("---")
    c1,c2 = st.columns([2,1])
    with c1:
        st.markdown('<p class="section-title">Mapa de inmuebles</p>',unsafe_allow_html=True)
        if len(df_fil)>0 and "latitude" in df_fil.columns:
            md = df_fil[["latitude","longitude","neighbourhood_group","price","precio_estimado","beneficio_neto_anual","rentabilidad_anual_pct","rentable_txt"]].dropna(subset=["latitude","longitude"]).head(5000)
            try:
                fig_map = px.scatter_map(md,lat="latitude",lon="longitude",color="rentable_txt",color_discrete_map={"Sí":"#6BBF8E","No":"#E07B54"},size="rentabilidad_anual_pct",size_max=12,hover_name="neighbourhood_group",hover_data={"price":True,"precio_estimado":True,"beneficio_neto_anual":True,"rentabilidad_anual_pct":True,"latitude":False,"longitude":False},zoom=11,center={"lat":40.4168,"lon":-3.7038},map_style="open-street-map",labels={"rentable_txt":"Rentable","price":"Precio/noche (€)","precio_estimado":"Precio compra (€)","beneficio_neto_anual":"Beneficio neto (€/año)","rentabilidad_anual_pct":"Rentabilidad (%)"})
            except Exception:
                fig_map = px.scatter_mapbox(md,lat="latitude",lon="longitude",color="rentable_txt",color_discrete_map={"Sí":"#6BBF8E","No":"#E07B54"},size="rentabilidad_anual_pct",size_max=12,hover_name="neighbourhood_group",zoom=11,center={"lat":40.4168,"lon":-3.7038},mapbox_style="open-street-map")
            fig_map.update_layout(paper_bgcolor=DARK,margin=dict(l=0,r=0,t=0,b=0),height=450,legend=dict(font=dict(color="#333")))
            st.plotly_chart(fig_map,use_container_width=True)
    with c2:
        st.markdown('<p class="section-title">Rentabilidad por distrito</p>',unsafe_allow_html=True)
        if len(df_fil)>0:
            td = df_fil.groupby("neighbourhood_group").agg(n=("price","count"),rentabilidad=("rentabilidad_anual_pct","median")).reset_index()
            fig_tree = px.treemap(td,path=["neighbourhood_group"],values="n",color="rentabilidad",color_continuous_scale=["#3A3A3A","#5B8DB8","#FF385C"],hover_data={"rentabilidad":":.1f"},labels={"neighbourhood_group":"Distrito","n":"Inmuebles","rentabilidad":"Rentabilidad (%)"})
            fig_tree.update_layout(paper_bgcolor=CARD,margin=dict(l=0,r=0,t=0,b=0),height=220,font_color=WHITE)
            st.plotly_chart(fig_tree,use_container_width=True)
        st.markdown('<p class="section-title">Resumen de la selección</p>',unsafe_allow_html=True)
        if len(df_fil)>0:
            for k,v in {"Precio/noche mediano":f"{df_fil['price'].median():,.0f} €","Precio compra mediano":f"{df_fil['precio_estimado'].median():,.0f} €","Beneficio neto mediano":f"{df_fil['beneficio_neto_anual'].median():,.0f} €/año","Rentabilidad mediana":f"{df_fil['rentabilidad_anual_pct'].median():.1f} %","% Rentables":f"{(df_fil['rentable_txt']=='Sí').mean()*100:.1f} %"}.items():
                st.markdown(f"**{k}:** {v}")
