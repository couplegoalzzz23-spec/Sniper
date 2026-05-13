import streamlit as st
import requests
import re
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import plotly.express as px

# =====================================
# 🚀 DATA MASTER LANUD INDONESIA
# =====================================
# Data ini menghubungkan Nama Lanud, ICAO (untuk METAR), dan ADM1 (untuk BMKG)
LANUD_DATA = [
    {"nama": "Lanud Roesmin Nurjadin (Pekanbaru)", "icao": "WIBB", "adm1": "14"},
    {"nama": "Lanud Halim Perdanakusuma (Jakarta)", "icao": "WIHH", "adm1": "31"},
    {"nama": "Lanud Atang Sendjaja (Bogor)", "icao": "WIAW", "adm1": "32"},
    {"nama": "Lanud Iswahjudi (Madiun)", "icao": "WARR", "adm1": "35"},
    {"nama": "Lanud Sultan Hasanuddin (Makassar)", "icao": "WAAA", "adm1": "73"},
    {"nama": "Lanud Silas Papare (Jayapura)", "icao": "WAJJ", "adm1": "94"},
    {"nama": "Lanud Supadio (Pontianak)", "icao": "WIOO", "adm1": "61"},
    {"nama": "Lanud Soewondo (Medan)", "icao": "WIMK", "adm1": "12"},
    {"nama": "Lanud Abdulrachman Saleh (Malang)", "icao": "WARA", "adm1": "35"},
    {"nama": "Lanud Sam Ratulangi (Manado)", "icao": "WAMM", "adm1": "71"},
    {"nama": "Lanud El Tari (Kupang)", "icao": "WATT", "adm1": "53"},
]
df_lanud = pd.DataFrame(LANUD_DATA)

# =====================================
# 🌑 CSS — MILITARY STYLE
# =====================================
st.set_page_config(page_title="Tactical Weather Ops", layout="wide")
st.markdown("""
<style>
body {background-color: #0b0c0c; color: #cfd2c3; font-family: "Consolas", "Roboto Mono", monospace;}
h1, h2, h3, h4 {color: #a9df52; text-transform: uppercase; letter-spacing: 1px;}
section[data-testid="stSidebar"] {background-color: #111; color: #d0d3ca;}
.stButton>button {background-color: #1a2a1f; color: #a9df52; border: 1px solid #3f4f3f; border-radius: 8px; font-weight: bold;}
div[data-testid="stMetricValue"] {color: #a9df52 !important;}
.radar {position: relative; width: 150px; height: 150px; border-radius: 50%; border: 2px solid #33ff55; overflow: hidden; margin: auto; box-shadow: 0 0 15px #33ff55;}
.radar:before {content: ""; position: absolute; top: 0; left: 0; width: 50%; height: 2px; background: #33ff55; transform-origin: 100% 50%; animation: sweep 2.5s linear infinite;}
@keyframes sweep {from { transform: rotate(0deg); } to { transform: rotate(360deg); }}
</style>
""", unsafe_allow_html=True)

# =====================================
# 🛰️ SIDEBAR (GLOBAL CONTROL)
# =====================================
with st.sidebar:
    st.title("🛰️ OPS CONTROL")
    selected_lanud_name = st.selectbox("🎯 SELECT LANUD", options=df_lanud["nama"].tolist())
    
    # Ambil data spesifik berdasarkan pilihan
    target_data = df_lanud[df_lanud["nama"] == selected_lanud_name].iloc[0]
    STATION_ICAO = target_data["icao"]
    ADM1_CODE = target_data["adm1"]
    
    st.markdown(f"**ICAO:** `{STATION_ICAO}`  \n**PROV CODE:** `{ADM1_CODE}`")
    st.markdown("<div class='radar'></div>", unsafe_allow_html=True)
    st.info(f"Target: {selected_lanud_name}")
    st.markdown("---")
    st.caption("Tactical Weather System v2.0")

# =====================================
# 🔹 TAB NAVIGASI
# =====================================
tab1, tab2 = st.tabs([f"📄 METAR {STATION_ICAO}", "🛰️ BMKG Tactical Forecast"])

# =====================================
# TAB 1: QAM METAR
# =====================================
with tab1:
    st.title("QAM METEOROLOGICAL REPORT")
    st.subheader(f"{selected_lanud_name} — {STATION_ICAO}")

    METAR_API = "https://aviationweather.gov/api/data/metar"

    def fetch_metar(icao):
        r = requests.get(METAR_API, params={"ids": icao, "hours": 0}, timeout=10)
        return r.text.strip()

    def parse_numeric_metar(m):
        t = re.search(r' (\d{2})(\d{2})(\d{2})Z', m)
        if not t: return None
        data = {"time": datetime.strptime(t.group(0).strip(), "%d%H%MZ"),
                "wind": None, "temp": None, "dew": None, "qnh": None, "vis": None,
                "RA": "RA" in m, "TS": "TS" in m, "FG": "FG" in m}
        w = re.search(r'(\d{3})(\d{2})KT', m)
        if w: data["wind"] = int(w.group(2))
        td = re.search(r' (M?\d{2})/(M?\d{2})', m)
        if td:
            data["temp"] = int(td.group(1).replace("M", "-"))
            data["dew"] = int(td.group(2).replace("M", "-"))
        q = re.search(r' Q(\d{4})', m)
        if q: data["qnh"] = int(q.group(1))
        v = re.search(r' (\d{4}) ', m)
        if v: data["vis"] = int(v.group(1))
        return data

    try:
        current_metar = fetch_metar(STATION_ICAO)
        if current_metar:
            st.code(current_metar, language="bash")
            m_data = parse_numeric_metar(current_metar)
            
            c1, c2, c3, c4 = st.columns(4)
            if m_data:
                c1.metric("WIND", f"{m_data['wind']} KT" if m_data['wind'] else "-")
                c2.metric("TEMP", f"{m_data['temp']} °C" if m_data['temp'] else "-")
                c3.metric("VIS", f"{m_data['vis']} m" if m_data['vis'] else "-")
                c4.metric("QNH", f"{m_data['qnh']} hPa" if m_data['qnh'] else "-")
        else:
            st.warning(f"No active METAR for {STATION_ICAO}")
    except Exception as e:
        st.error(f"Error fetching METAR: {e}")

# =====================================
# TAB 2: BMKG Tactical Forecast
# =====================================
with tab2:
    st.title("Tactical Forecast Operations")
    st.markdown(f"**Region Intelligence: Province Code {ADM1_CODE}**")

    API_BASE = "https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
    MS_TO_KT = 1.94384

    @st.cache_data(ttl=300)
    def fetch_forecast(adm_code):
        resp = requests.get(API_BASE, params={"adm1": adm_code}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def flatten_cuaca_entry(entry):
        rows = []
        lokasi = entry.get("lokasi", {})
        for group in entry.get("cuaca", []):
            for obs in group:
                r = obs.copy()
                r.update({"adm2": lokasi.get("adm2"), "kotkab": lokasi.get("kotkab"), 
                          "lon": lokasi.get("lon"), "lat": lokasi.get("lat")})
                r["local_datetime_dt"] = pd.to_datetime(r.get("local_datetime"))
                rows.append(r)
        df = pd.DataFrame(rows)
        for c in ["t", "tp", "ws", "hu"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
        return df

    try:
        raw_data = fetch_forecast(ADM1_CODE)
        entries = raw_data.get("data", [])
        
        if entries:
            # Dropdown untuk memilih kabupaten di dalam provinsi tersebut
            loc_list = [e.get("lokasi", {}).get("kotkab", "Unknown") for e in entries]
            target_city = st.selectbox("🎯 Select Tactical Area (District)", options=loc_list)
            
            # Filter data sesuai kabupaten terpilih
            selected_entry = next(e for e in entries if e["lokasi"]["kotkab"] == target_city)
            df_f = flatten_cuaca_entry(selected_entry)
            df_f["ws_kt"] = df_f["ws"] * MS_TO_KT

            # Visualisasi Chart
            st.subheader(f"Weather Trend: {target_city}")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
            fig.add_trace(go.Scatter(x=df_f["local_datetime_dt"], y=df_f["t"], name="Temp (°C)", line=dict(color='#a9df52')), row=1, col=1)
            fig.add_trace(go.Bar(x=df_f["local_datetime_dt"], y=df_f["tp"], name="Rain (mm)", marker_color='#00ffbf'), row=2, col=1)
            fig.update_layout(height=500, template="plotly_dark", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Map
            st.markdown("---")
            lat, lon = float(selected_entry["lokasi"]["lat"]), float(selected_entry["lokasi"]["lon"])
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

    except Exception as e:
        st.error(f"Failed to fetch Forecast data: {e}")

# =====================================
# FOOTER
# =====================================
st.markdown("""
<hr>
<div style="text-align:center; color:#7a7; font-size:0.8rem;">
Ops Dashboard v2.0 | Integrated Lanud Database | BMKG & AviationWeather Real-time
</div>
""", unsafe_allow_html=True)
