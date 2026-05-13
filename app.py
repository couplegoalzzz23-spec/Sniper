import streamlit as st

# MUST BE FIRST: Page Configuration
st.set_page_config(page_title="Tactical Weather Ops — BMKG", layout="wide")

import requests
import re
from datetime import datetime
import pandas as pd
import plotly.express as px
import os

# =====================================
# LOAD DATA LANUD (Standard ICAO & BPS)
# =====================================
LANUD_CSV = os.path.join(os.path.dirname(__file__), "kode_wilayah_lanud_indonesia.csv")

@st.cache_data
def load_lanud_codes():
    try:
        # Membaca CSV dengan kolom: Nama Lanud, ICAO, Lokasi, Kode Wilayah
        df = pd.read_csv(LANUD_CSV)
        return df
    except Exception as e:
        st.error(f"Gagal memuat database Lanud: {e}")
        st.stop()

lanud_df = load_lanud_codes()

# =====================================
# CSS MILITARY STYLE
# =====================================
st.markdown("""
<style>
body {background-color: #0b0c0c; color: #cfd2c3; font-family: Consolas;}
h1, h2, h3, h4 {color: #a9df52; text-transform: uppercase;}
section[data-testid="stSidebar"] {background-color: #111;}
.radar {
    position: relative; width: 160px; height: 160px; border-radius: 50%;
    border:2px solid #33ff55; overflow:hidden; margin:auto; box-shadow:0 0 20px #33ff55;
}
.radar:before {
    content:""; position:absolute; top:0; left:0; width:50%; height:2px;
    background:linear-gradient(90deg,#33ff55,transparent);
    transform-origin:100% 50%; animation:sweep 2.5s linear infinite;
}
@keyframes sweep { from {transform:rotate(0deg);} to {transform:rotate(360deg);} }
</style>
""", unsafe_allow_html=True)

# =====================================
# SIDEBAR CONTROLS (Dinamis)
# =====================================
with st.sidebar:
    st.title("🛰️ Tactical Controls")
    
    selected_name = st.selectbox(
        "✈️ Select Indonesian Air Base",
        lanud_df["Nama Lanud"]
    )
    
    # Ambil data spesifik baris yang dipilih
    row = lanud_df[lanud_df["Nama Lanud"] == selected_name].iloc[0]
    
    target_icao = row["ICAO"]
    target_code = str(row["Kode Wilayah"])
    target_loc = row["Lokasi"]

    st.info(f"""
    **CURRENT STATION**
    - ICAO: {target_icao}
    - Sector: {target_code}
    - Location: {target_loc}
    """)
    
    st.markdown("<div class='radar'></div>", unsafe_allow_html=True)
    show_map = st.checkbox("Show Deployment Map", True)

# =====================================
# TABS SYSTEM
# =====================================
tab1, tab2 = st.tabs(["📄 QAM METAR REPORT", "🛰️ BMKG TACTICAL FORECAST"])

# =====================================
# TAB 1: QAM METAR (Disesuaikan ICAO)
# =====================================
with tab1:
    st.title(f"QAM METEOROLOGICAL REPORT")
    st.subheader(f"STATION: {selected_name} — {target_icao}")

    # Menggunakan API Aviation Weather yang valid
    METAR_API = f"https://aviationweather.gov/api/data/metar?ids={target_icao}&format=raw"

    def fetch_metar():
        try:
            r = requests.get(METAR_API, timeout=10)
            if r.status_code == 200 and r.text.strip():
                return r.text.strip()
            return f"No METAR information available for {target_icao} at this time."
        except:
            return "Connection to Aviation Weather Server failed."

    st.code(fetch_metar())
    st.caption("Data source: AviationWeather.gov (NOAA)")

# =====================================
# TAB 2: BMKG FORECAST (Fix Error 404)
# =====================================
with tab2:
    MS_TO_KT = 1.94384

    @st.cache_data(ttl=300)
    def fetch_forecast(code):
        # Fix 404: Menggunakan endpoint df/v1/forecast/ dengan parameter area
        # Beberapa server memerlukan format tanpa suffix jika adm2 gagal
        level = "adm2" if "." in code else "adm1"
        url = f"https://cuaca.bmkg.go.id/api/df/v1/forecast/{level}"
        
        try:
            r = requests.get(url, params={level: code}, timeout=15)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError:
            # Fallback jika adm2 gagal, coba akses via area general
            return None

    def flatten(entry):
        rows = []
        lokasi = entry.get("lokasi", {})
        for group in entry.get("cuaca", []):
            for obs in group:
                r = obs.copy()
                r.update({
                    "lat": lokasi.get("lat"),
                    "lon": lokasi.get("lon"),
                    "kotkab": lokasi.get("kotkab")
                })
                rows.append(r)
        df = pd.DataFrame(rows)
        for c in ["t","tp","ws","hu","wd_deg"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df["local_datetime_dt"] = pd.to_datetime(df["local_datetime"])
        return df

    raw = fetch_forecast(target_code)

    if raw and "data" in raw:
        entries = raw.get("data", [])
        mapping = { (e['lokasi'].get('kotkab') or "Area"): e for e in entries }
        
        loc_choice = st.selectbox("🎯 Select Tactical Point", list(mapping.keys()))
        df_forecast = flatten(mapping[loc_choice])
        df_forecast["ws_kt"] = df_forecast["ws"] * MS_TO_KT
        
        now = df_forecast.iloc[0]

        # Metrics
        st.subheader("⚡ Current Tactical Status")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TEMP", f"{now['t']}°C")
        c2.metric("HUMIDITY", f"{now['hu']}%")
        c3.metric("WIND", f"{now['ws_kt']:.1f} KT")
        c4.metric("PRECIP", f"{now['tp']} mm")

        # Visualizations
        st.subheader("📊 Operational Trends")
        st.plotly_chart(px.line(df_forecast, x="local_datetime_dt", y="t", title="Temperature Trend"), use_container_width=True)
        st.plotly_chart(px.line(df_forecast, x="local_datetime_dt", y="ws_kt", title="Wind Speed (KT)"), use_container_width=True)

        if show_map:
            st.subheader("🗺️ Deployment Map")
            st.map(pd.DataFrame({"lat": [float(now["lat"])], "lon": [float(now["lon"])]}))
    else:
        st.error(f"Tactical Error: Data for sector {target_code} is currently restricted or not found on BMKG server.")
        st.info("Saran: Pastikan kode wilayah di CSV sudah benar (ADM2) atau hubungi admin sistem.")

# FOOTER
st.markdown("""
---
<div style="text-align:center; color:#7a7; font-size:0.8em;">
Tactical Weather Dashboard | Resti Maulina C.C. | STMKG 7C
</div>
""", unsafe_allow_html=True)
