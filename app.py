import streamlit as st
st.set_page_config(page_title="Tactical Weather Ops — BMKG", layout="wide")

import requests
import re
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import plotly.express as px
import os

# =====================================
# LOAD CSV LANUD
# =====================================
LANUD_CSV = os.path.join(os.path.dirname(__file__), "kode_wilayah_lanud_indonesia.csv")

@st.cache_data
def load_lanud_codes():
    try:
        df = pd.read_csv(LANUD_CSV)
    except:
        df = pd.read_csv(LANUD_CSV, header=None)

    if df.shape[1] < 2:
        st.error("CSV minimal 2 kolom")
        st.stop()

    clean = pd.DataFrame({
        "Nama Lanud": df.iloc[:, 0].astype(str).str.strip(),
        "Kode Wilayah": df.iloc[:, 1].astype(str).str.strip()
    })

    if df.shape[1] >= 3:
        clean["Lokasi"] = df.iloc[:, 2].astype(str).str.strip()
    else:
        clean["Lokasi"] = "-"

    return clean

lanud_df = load_lanud_codes()

# =====================================
# CSS — MILITARY STYLE
# =====================================
st.markdown("""
<style>
body {background-color: #0b0c0c; color: #cfd2c3; font-family: Consolas;}
h1, h2, h3, h4 {color: #a9df52;}
section[data-testid="stSidebar"] {background-color: #111;}
.stButton>button {
    background-color:#1a2a1f;
    color:#a9df52;
    border:1px solid #3f4f3f;
}
.radar {
position: relative;
width: 160px;
height: 160px;
border-radius: 50%;
border:2px solid #33ff55;
overflow:hidden;
margin:auto;
box-shadow:0 0 20px #33ff55;
}
.radar:before {
content:"";
position:absolute;
top:0;
left:0;
width:50%;
height:2px;
background:linear-gradient(90deg,#33ff55,transparent);
transform-origin:100% 50%;
animation:sweep 2.5s linear infinite;
}
@keyframes sweep {
from {transform:rotate(0deg);}
to {transform:rotate(360deg);}
}
</style>
""", unsafe_allow_html=True)

# =====================================
# TABS
# =====================================
tab1, tab2 = st.tabs(["📄 QAM METAR WIBB", "🛰️ BMKG Tactical Forecast"])

# =====================================
# TAB 1
# =====================================
with tab1:
    st.title("QAM METEOROLOGICAL REPORT")
    st.subheader("Lanud Roesmin Nurjadin — WIBB")

    METAR_API = "https://aviationweather.gov/api/data/metar"

    def fetch_metar():
        r = requests.get(METAR_API, params={"ids":"WIBB","hours":0}, timeout=10)
        return r.text.strip()

    metar = fetch_metar()
    st.code(metar)

# =====================================
# TAB 2
# =====================================
with tab2:

    API_BASE = "https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
    MS_TO_KT = 1.94384

    @st.cache_data(ttl=300)
    def fetch_forecast(adm1):
        r = requests.get(API_BASE, params={"adm1":adm1}, timeout=10)
        return r.json()

    def flatten(entry):
        rows=[]
        lokasi=entry.get("lokasi",{})

        for group in entry.get("cuaca",[]):
            for obs in group:
                r=obs.copy()
                r["lat"]=lokasi.get("lat")
                r["lon"]=lokasi.get("lon")
                r["kotkab"]=lokasi.get("kotkab")
                rows.append(r)

        df=pd.DataFrame(rows)

        for c in ["t","tp","ws","hu","wd_deg"]:
            if c in df.columns:
                df[c]=pd.to_numeric(df[c], errors="coerce")

        df["local_datetime_dt"]=pd.to_datetime(df["local_datetime"])
        return df

    # =====================================
    # SIDEBAR
    # =====================================
    with st.sidebar:
        st.title("🛰️ Tactical Controls")

        selected_lanud = st.selectbox(
            "✈️ Select Indonesian Air Base",
            lanud_df["Nama Lanud"]
        )

        row = lanud_df[
            lanud_df["Nama Lanud"] == selected_lanud
        ].iloc[0]

        adm1 = row["Kode Wilayah"]

        st.info(f"""
Lanud: {row['Nama Lanud']}

Lokasi: {row['Lokasi']}

Kode BMKG: {adm1}
""")

        st.markdown("<div class='radar'></div>", unsafe_allow_html=True)

        show_map = st.checkbox("Show Map", True)
        show_table = st.checkbox("Show Table", False)

    # =====================================
    # FETCH DATA
    # =====================================
    st.title("Tactical Weather Operations Dashboard")

    raw = fetch_forecast(adm1)

    entries = raw.get("data", [])

    if not entries:
        st.warning("No data available")
        st.stop()

    mapping = {}

    for e in entries:
        lok=e.get("lokasi",{})
        label=lok.get("kotkab") or "Unknown"
        mapping[label]=e

    loc_choice = st.selectbox(
        "🎯 Select Location",
        list(mapping.keys())
    )

    selected_entry = mapping[loc_choice]

    df = flatten(selected_entry)

    if df.empty:
        st.warning("No weather data")
        st.stop()

    df["ws_kt"] = df["ws"] * MS_TO_KT

    now = df.iloc[0]

    # =====================================
    # METRICS
    # =====================================
    st.subheader("⚡ Tactical Weather Status")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("TEMP", f"{now['t']}°C")
    c2.metric("HUMIDITY", f"{now['hu']}%")
    c3.metric("WIND", f"{now['ws_kt']:.1f} KT")
    c4.metric("RAIN", f"{now['tp']} mm")

    # =====================================
    # TRENDS
    # =====================================
    st.subheader("📊 Parameter Trends")

    col1,col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            px.line(df, x="local_datetime_dt", y="t", title="Temperature"),
            use_container_width=True
        )

    with col2:
        st.plotly_chart(
            px.line(df, x="local_datetime_dt", y="ws_kt", title="Wind Speed"),
            use_container_width=True
        )

    # =====================================
    # MAP
    # =====================================
    if show_map:
        st.subheader("🗺️ Tactical Map")

        st.map(pd.DataFrame({
            "lat":[float(df.iloc[0]["lat"])],
            "lon":[float(df.iloc[0]["lon"])]
        }))

    # =====================================
    # TABLE
    # =====================================
    if show_table:
        st.subheader("📋 Forecast Table")
        st.dataframe(df)

    # =====================================
    # DOWNLOAD
    # =====================================
    st.subheader("💾 Export Data")

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        file_name=f"{adm1}_{loc_choice}.csv"
    )

    # =====================================
    # FOOTER
    # =====================================
    st.markdown("""
---
<div style="text-align:center;color:#7a7;">
Tactical Weather Ops Dashboard — BMKG
</div>
""", unsafe_allow_html=True)
