import streamlit as st
st.set_page_config(page_title="Tactical Weather Ops", layout="wide")

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
# CSV LANUD
# =====================================
LANUD_CSV = "kode_wilayah_lanud_indonesia.csv"

@st.cache_data
def load_lanud_codes():
    try:
        df = pd.read_csv(LANUD_CSV, header=0)
    except:
        df = pd.read_csv(LANUD_CSV, header=None)

    if df.shape[1] < 2:
        st.error("CSV harus minimal 2 kolom")
        st.stop()

    # ambil kolom berdasarkan posisi
    lanud = df.iloc[:, 0].astype(str)
    kode = df.iloc[:, 1].astype(str)

    lokasi = df.iloc[:, 2].astype(str) if df.shape[1] >= 3 else "-"

    clean = pd.DataFrame({
        "Nama Lanud": lanud,
        "Kode Wilayah": kode,
        "Lokasi": lokasi
    })

    return clean

lanud_df = load_lanud_codes()

# =====================================
# CSS
# =====================================
st.markdown("""
<style>
body {background-color:#0b0c0c;color:#cfd2c3;}
h1,h2,h3 {color:#a9df52;}
section[data-testid="stSidebar"] {background-color:#111;}
</style>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📄 QAM METAR WIBB", "🛰️ BMKG Tactical Forecast"])

# =====================================
# TAB 1
# =====================================
with tab1:
    st.title("QAM METAR")

    METAR_API = "https://aviationweather.gov/api/data/metar"

    def fetch_metar():
        r = requests.get(METAR_API, params={"ids":"WIBB","hours":0})
        return r.text.strip()

    st.code(fetch_metar())

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
                obs["lat"]=lokasi.get("lat")
                obs["lon"]=lokasi.get("lon")
                obs["kotkab"]=lokasi.get("kotkab")
                rows.append(obs)

        df=pd.DataFrame(rows)

        for c in ["t","tp","ws","hu"]:
            if c in df.columns:
                df[c]=pd.to_numeric(df[c],errors="coerce")

        df["local_datetime_dt"]=pd.to_datetime(df["local_datetime"])

        return df

    # SIDEBAR
    with st.sidebar:
        st.title("🛰️ Tactical Controls")

        selected_lanud = st.selectbox(
            "✈️ Select Lanud",
            lanud_df["Nama Lanud"]
        )

        row = lanud_df[
            lanud_df["Nama Lanud"] == selected_lanud
        ].iloc[0]

        adm1 = row["Kode Wilayah"]

        st.info(f"""
Lanud: {row['Nama Lanud']}

Lokasi: {row['Lokasi']}

Kode: {adm1}
""")

        show_map = st.checkbox("Show Map", True)
        show_table = st.checkbox("Show Table", False)

    st.title("Tactical Weather Dashboard")

    raw = fetch_forecast(adm1)

    entries = raw.get("data",[])

    if not entries:
        st.warning("No data")
        st.stop()

    mapping={}

    for e in entries:
        lok=e.get("lokasi",{})
        label=lok.get("kotkab","Unknown")
        mapping[label]=e

    loc_choice=st.selectbox(
        "Select Location",
        list(mapping.keys())
    )

    df=flatten(mapping[loc_choice])

    df["ws_kt"]=df["ws"]*MS_TO_KT

    now=df.iloc[0]

    c1,c2,c3,c4=st.columns(4)

    c1.metric("TEMP",f"{now['t']}°C")
    c2.metric("HUMIDITY",f"{now['hu']}%")
    c3.metric("WIND",f"{now['ws_kt']:.1f} KT")
    c4.metric("RAIN",f"{now['tp']} mm")

    st.plotly_chart(
        px.line(df,x="local_datetime_dt",y="t"),
        use_container_width=True
    )

    st.plotly_chart(
        px.line(df,x="local_datetime_dt",y="ws_kt"),
        use_container_width=True
    )

    if show_map:
        st.map(pd.DataFrame({
            "lat":[float(df.iloc[0]["lat"])],
            "lon":[float(df.iloc[0]["lon"])]
        }))

    if show_table:
        st.dataframe(df)

    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        file_name=f"{adm1}.csv"
    )
