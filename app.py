import streamlit as st
import requests
import re
import io
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import plotly.express as px

# =====================================
# 🌑 DATA LANUD INDONESIA (INTERNAL CSV)
# =====================================
# Mapping Lanud ke Kode Provinsi (ADM1) BMKG untuk Query API
lanud_csv_data = """Nama_Lanud,ICAO,Kota_Kab,ADM1_Code
Lanud Roesmin Nurjadin,WIBB,Pekanbaru,14
Lanud Halim Perdanakusuma,WIHH,Jakarta Timur,31
Lanud Atang Sendjaja,WIAW,Bogor,32
Lanud Iswahjudi,WIAI,Magetan,35
Lanud Abdul Rachman Saleh,WARA,Malang,35
Lanud Sultan Hasanuddin,WAAA,Maros,73
Lanud Supadio,WIOO,Kubu Raya,61
Lanud Soewondo,WIMK,Medan,12
Lanud Sri Mulyono Herlambang,WIPA,Palembang,16
Lanud Raden Sadjad,WION,Natuna,21
Lanud Sam Ratulangi,WAMM,Manado,71
Lanud El Tari,WATT,Kupang,53
Lanud Manuhua,WABB,Biak Numfor,91
Lanud Silas Papare,WAJJ,Jayapura,91
Lanud Anang Busra,WAXX,Tarakan,65
"""
df_lanud = pd.read_csv(io.StringIO(lanud_csv_data))

# =====================================
# 🌑 CSS — MILITARY STYLE + RADAR ANIMATION
# =====================================
st.set_page_config(page_title="Tactical Weather Ops — BMKG", layout="wide")

st.markdown("""
<style>
body {background-color: #0b0c0c; color: #cfd2c3; font-family: "Consolas", "Roboto Mono", monospace;}
h1, h2, h3, h4 {color: #a9df52; text-transform: uppercase; letter-spacing: 1px;}
section[data-testid="stSidebar"] {background-color: #111; color: #d0d3ca;}
.stButton>button {background-color: #1a2a1f; color: #a9df52; border: 1px solid #3f4f3f; border-radius: 8px; font-weight: bold;}
.stButton>button:hover {background-color: #2b3b2b; border-color: #a9df52;}
div[data-testid="stMetricValue"] {color: #a9df52 !important;}
.radar {position: relative; width: 160px; height: 160px; border-radius: 50%; background: radial-gradient(circle, rgba(20,255,50,0.05) 20%, transparent 21%), radial-gradient(circle, rgba(20,255,50,0.1) 10%, transparent 11%); background-size: 20px 20px; border: 2px solid #33ff55; overflow: hidden; margin: auto; box-shadow: 0 0 20px #33ff55;}
.radar:before {content: ""; position: absolute; top: 0; left: 0; width: 50%; height: 2px; background: linear-gradient(90deg, #33ff55, transparent); transform-origin: 100% 50%; animation: sweep 2.5s linear infinite;}
@keyframes sweep {from { transform: rotate(0deg); } to { transform: rotate(360deg); }}
hr, .stDivider {border-top: 1px solid #2f3a2f;}
</style>
""", unsafe_allow_html=True)

# =====================================
# 🔹 TAB NAVIGASI
# =====================================
tab1, tab2 = st.tabs(["📄 QAM METAR WIBB", "🛰️ BMKG Tactical Forecast (Lanud)"])

# =====================================
# TAB 1: QAM METAR
# =====================================
with tab1:
    st.title("QAM METEOROLOGICAL REPORT")
    st.subheader("Lanud Roesmin Nurjadin — WIBB")

    METAR_API = "https://aviationweather.gov/api/data/metar"
    SATELLITE_HIMA_RIAU = "http://202.90.198.22/IMAGE/HIMA/H08_RP_Riau.png"

    def fetch_metar():
        r = requests.get(METAR_API, params={"ids": "WIBB", "hours": 0}, timeout=10)
        return r.text.strip()

    def fetch_metar_history(hours=24):
        r = requests.get(METAR_API, params={"ids": "WIBB", "hours": hours}, timeout=10)
        return r.text.strip().splitlines()

    # Parsers (Simple Regex)
    def wind(m):
        x = re.search(r'(\d{3})(\d{2})KT', m)
        return f"{x.group(1)}° / {x.group(2)} kt" if x else "-"

    def visibility(m):
        x = re.search(r' (\d{4}) ', m)
        return f"{x.group(1)} m" if x else "-"

    def temp_dew(m):
        x = re.search(r' (M?\d{2})/(M?\d{2})', m)
        return f"{x.group(1)} / {x.group(2)} °C" if x else "-"

    def qnh(m):
        x = re.search(r' Q(\d{4})', m)
        return f"{x.group(1)} hPa" if x else "-"

    def parse_numeric_metar(m):
        t = re.search(r' (\d{2})(\d{2})(\d{2})Z', m)
        if not t: return None
        data = {"time": datetime.strptime(t.group(0).strip(), "%d%H%MZ"), "wind": None, "temp": None, "dew": None, "qnh": None, "vis": None, "RA": "RA" in m, "TS": "TS" in m, "FG": "FG" in m}
        w = re.search(r'(\d{3})(\d{2})KT', m); data["wind"] = int(w.group(2)) if w else None
        td = re.search(r' (M?\d{2})/(M?\d{2})', m)
        if td: data["temp"], data["dew"] = int(td.group(1).replace("M", "-")), int(td.group(2).replace("M", "-"))
        q = re.search(r' Q(\d{4})', m); data["qnh"] = int(q.group(1)) if q else None
        v = re.search(r' (\d{4}) ', m); data["vis"] = int(v.group(1)) if v else None
        return data

    metar = fetch_metar()
    st.code(metar)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("WIND", wind(metar))
    c2.metric("VIS", visibility(metar))
    c3.metric("TEMP/DEW", temp_dew(metar))
    c4.metric("QNH", qnh(metar))

    st.image(SATELLITE_HIMA_RIAU, caption="Satellite Imagery Riau Sector", use_container_width=True)

# =====================================
# TAB 2: BMKG Tactical Forecast (MODIFIED)
# =====================================
with tab2:
    API_BASE = "https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
    MS_TO_KT = 1.94384

    @st.cache_data(ttl=300)
    def fetch_forecast(adm1_code):
        params = {"adm1": str(adm1_code)}
        resp = requests.get(API_BASE, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def flatten_cuaca_entry(entry):
        rows = []
        lokasi = entry.get("lokasi", {})
        for group in entry.get("cuaca", []):
            for obs in group:
                r = obs.copy()
                r.update({
                    "adm2": lokasi.get("kotkab") or lokasi.get("adm2"),
                    "lon": lokasi.get("lon"),
                    "lat": lokasi.get("lat"),
                })
                r["local_datetime_dt"] = pd.to_datetime(r.get("local_datetime"))
                rows.append(r)
        df = pd.DataFrame(rows)
        for c in ["t", "tp", "wd_deg", "ws", "hu"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
        return df

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.title("🛰️ Tactical Controls")
        
        # DROPDOWN LANUD (Menggantikan Input Manual ADM1)
        selected_lanud_name = st.selectbox("🎯 Target Lanud Area", options=df_lanud["Nama_Lanud"].tolist())
        
        # Ambil metadata lanud yang dipilih
        lanud_info = df_lanud[df_lanud["Nama_Lanud"] == selected_lanud_name].iloc[0]
        adm1_query = lanud_info["ADM1_Code"]
        target_city = lanud_info["Kota_Kab"]
        
        st.markdown("<div class='radar'></div>", unsafe_allow_html=True)
        st.info(f"Target: {selected_lanud_name} ({lanud_info['ICAO']})\nProvince Code: {adm1_query}")
        
        refresh = st.button("🔄 Refresh Intelligence")
        st.markdown("---")
        show_map = st.checkbox("Show Map", value=True)
        st.caption("Military Ops Dashboard v2.0")

    st.title(f"Tactical Weather: {selected_lanud_name}")
    
    with st.spinner("🛰️ Acquiring regional intelligence..."):
        try:
            raw_data = fetch_forecast(adm1_query)
            entries = raw_data.get("data", [])
            
            # Mapping lokasi yang tersedia di provinsi tersebut
            loc_map = {}
            for e in entries:
                name = e.get("lokasi", {}).get("kotkab") or e.get("lokasi", {}).get("adm2")
                loc_map[name] = e
            
            # Auto-select lokasi yang paling cocok dengan Lanud (Kota_Kab)
            default_index = 0
            loc_list = list(loc_map.keys())
            if target_city in loc_list:
                default_index = loc_list.index(target_city)
            
            selected_city = st.selectbox("📍 Specific Sector", options=loc_list, index=default_index)
            
            # Data Processing
            df = flatten_cuaca_entry(loc_map[selected_city])
            df["ws_kt"] = df["ws"] * MS_TO_KT
            df = df.sort_values("local_datetime_dt")

            # Metrics
            st.markdown("---")
            now = df.iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("TEMP", f"{now['t']}°C")
            m2.metric("HUMIDITY", f"{now['hu']}%")
            m3.metric("WIND SPEED", f"{now['ws_kt']:.1f} KT")
            m4.metric("PRECIP", f"{now['tp']} mm")

            # Charts
            st.subheader("📊 Forecast Trends (72 Hours)")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
            fig.add_trace(go.Scatter(x=df["local_datetime_dt"], y=df["t"], name="Temp (°C)", line=dict(color='#a9df52', width=3)), row=1, col=1)
            fig.add_trace(go.Bar(x=df["local_datetime_dt"], y=df["ws_kt"], name="Wind (KT)", marker_color='#00ffbf'), row=2, col=1)
            fig.update_layout(height=500, template="plotly_dark", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            if show_map:
                st.subheader("🗺️ Tactical Map")
                map_df = pd.DataFrame({"lat": [float(df["lat"].iloc[0])], "lon": [float(df["lon"].iloc[0])]})
                st.map(map_df)

            st.download_button("⬇️ Export Sector Data (CSV)", df.to_csv(index=False), f"Ops_{selected_city}.csv")

        except Exception as e:
            st.error(f"Intelligence Failure: {e}")

# =====================================
# FOOTER
# =====================================
st.markdown("""
<hr>
<div style="text-align:center; color:#5f5; font-size:0.8rem; font-family:monospace;">
DATA_SOURCE: BMKG_CENTRAL_API | STATUS: OPERATIONAL | SECURITY_LEVEL: UNCLASSIFIED
</div>
""", unsafe_allow_html=True)
