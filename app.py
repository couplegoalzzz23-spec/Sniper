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
# 🌑 CSS — MILITARY STYLE + RADAR ANIMATION
# =====================================
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
# 📂 DATA LANUD INDONESIA (SESUAI INPUT USER)
# =====================================
LANUD_LIST = [
    {"nama": "Halim Perdanakusuma", "lokasi": "Jakarta Timur", "kode": "31.75"},
    {"nama": "Atang Sendjaja", "lokasi": "Kab. Bogor", "kode": "32.01"},
    {"nama": "Atang Sendjaja", "lokasi": "Kota Bogor", "kode": "32.71"},
    {"nama": "Suryadarma", "lokasi": "Kab. Subang", "kode": "32.13"},
    {"nama": "Husein Sastranegara", "lokasi": "Kab. Bandung", "kode": "32.04"},
    {"nama": "Husein Sastranegara", "lokasi": "Kab. Bandung Barat", "kode": "32.17"},
    {"nama": "Husein Sastranegara", "lokasi": "Kota Bandung", "kode": "32.73"},
    {"nama": "Sulaiman", "lokasi": "Kab. Bandung", "kode": "32.04"},
    {"nama": "Sulaiman", "lokasi": "Kab. Bandung Barat", "kode": "32.17"},
    {"nama": "Sulaiman", "lokasi": "Kota Bandung", "kode": "32.73"},
    {"nama": "Wiriadinata", "lokasi": "Kab. Tasikmalaya", "kode": "32.06"},
    {"nama": "Wiriadinata", "lokasi": "Kota Tasikmalaya", "kode": "32.78"},
    {"nama": "Sugiri Sukani", "lokasi": "Kab. Cirebon", "kode": "32.09"},
    {"nama": "Sugiri Sukani", "lokasi": "Kota Cirebon", "kode": "32.74"},
    {"nama": "Roesmin Nurjadin", "lokasi": "Kota Pekanbaru", "kode": "14.71"},
    {"nama": "Soewondo", "lokasi": "Kota Medan", "kode": "12.71"},
    {"nama": "Soewondo", "lokasi": "Kab. Sumedang", "kode": "32.11"},
    {"nama": "Sultan Iskandar Muda", "lokasi": "Kota Banda Aceh", "kode": "11.71"},
    {"nama": "Maimun Saleh", "lokasi": "Kota Sabang", "kode": "11.72"},
    {"nama": "Sutan Sjahrir", "lokasi": "Kab. Padang Lawas Utara", "kode": "12.20"},
    {"nama": "Sutan Sjahrir", "lokasi": "Kab. Padang Lawas", "kode": "12.21"},
    {"nama": "Sutan Sjahrir", "lokasi": "Kota Padang Sidempuan", "kode": "12.77"},
    {"nama": "Sutan Sjahrir", "lokasi": "Kab. Padang Pariaman", "kode": "13.05"},
    {"nama": "Sutan Sjahrir", "lokasi": "Kota Padang", "kode": "13.71"},
    {"nama": "Sutan Sjahrir", "lokasi": "Kota Padang Panjang", "kode": "13.74"},
    {"nama": "Raja Haji Fisabilillah", "lokasi": "Kota Tanjung Pinang", "kode": "21.72"},
    {"nama": "Hang Nadim", "lokasi": "Kota Batam", "kode": "21.71"},
    {"nama": "H. AS Hanandjoeddin", "lokasi": "Kab. Belitung", "kode": "19.02"},
    {"nama": "H. AS Hanandjoeddin", "lokasi": "Kab. Belitung Timur", "kode": "19.06"},
    {"nama": "Sri Mulyono Herlambang", "lokasi": "Kota Palembang", "kode": "16.71"},
    {"nama": "Pangeran M. Bun Yamin", "lokasi": "Kab. Tulang Bawang", "kode": "18.05"},
    {"nama": "Pangeran M. Bun Yamin", "lokasi": "Kab. Tulang Bawang Barat", "kode": "18.12"},
    {"nama": "Supadio", "lokasi": "Kota Pontianak", "kode": "61.71"},
    {"nama": "Harry Hadisoemantri", "lokasi": "Kab. Bengkayang", "kode": "61.07"},
    {"nama": "Iskandar", "lokasi": "Kab. Kotawaringin Barat", "kode": "62.01"},
    {"nama": "Syamsudin Noor", "lokasi": "Kota Banjarbaru", "kode": "63.72"},
    {"nama": "Dhomber", "lokasi": "Kota Balikpapan", "kode": "64.71"},
    {"nama": "Anang Busra", "lokasi": "Kota Tarakan", "kode": "65.71"},
    {"nama": "Abdulrachman Saleh", "lokasi": "Kab. Pemalang", "kode": "33.27"},
    {"nama": "Abdulrachman Saleh", "lokasi": "Kab. Malang", "kode": "35.07"},
    {"nama": "Abdulrachman Saleh", "lokasi": "Kota Malang", "kode": "35.73"},
    {"nama": "Iswahjudi", "lokasi": "Kab. Magetan", "kode": "35.20"},
    {"nama": "Adi Soemarmo", "lokasi": "Kab. Boyolali", "kode": "33.09"},
    {"nama": "Adisutjipto", "lokasi": "Kab. Sleman", "kode": "34.04"},
    {"nama": "Jenderal Besar Soedirman", "lokasi": "Kab. Purbalingga", "kode": "33.03"},
    {"nama": "Muljono", "lokasi": "Kab. Sidoarjo", "kode": "35.15"},
    {"nama": "El Tari", "lokasi": "Kab. Kupang", "kode": "53.01"},
    {"nama": "El Tari", "lokasi": "Kota Kupang", "kode": "53.71"},
    {"nama": "I Gusti Ngurah Rai", "lokasi": "Kab. Badung", "kode": "51.03"},
    {"nama": "Zainuddin Abdul Madjid", "lokasi": "Kota Mataram", "kode": "52.71"},
    {"nama": "Sultan Hasanuddin", "lokasi": "Kab. Maros", "kode": "73.09"},
    {"nama": "Haluoleo", "lokasi": "Kab. Konawe Selatan", "kode": "74.05"},
    {"nama": "Sam Ratulangi", "lokasi": "Kota Manado", "kode": "71.71"},
    {"nama": "Pattimura", "lokasi": "Kota Ambon", "kode": "81.71"},
    {"nama": "Leo Wattimena", "lokasi": "Kab. Pulau Morotai", "kode": "82.07"},
    {"nama": "Dominicus Dumatubun", "lokasi": "Kab. Maluku Tenggara", "kode": "81.02"},
    {"nama": "Silas Papare", "lokasi": "Kab. Jayapura", "kode": "91.03"},
    {"nama": "Silas Papare", "lokasi": "Kota Jayapura", "kode": "91.71"},
    {"nama": "Manuhua", "lokasi": "Kab. Biak Numfor", "kode": "91.06"},
    {"nama": "Yohanis Kapiyau", "lokasi": "Kab. Mimika", "kode": "91.09"},
    {"nama": "Johannes Abraham Dimara", "lokasi": "Kab. Merauke", "kode": "91.01"},
]

LANUD_OPTIONS = [f"Lanud {d['nama']} - {d['lokasi']}" for d in LANUD_LIST]

# =====================================
# 🔹 TAB NAVIGASI
# =====================================
tab1, tab2 = st.tabs(["📄 QAM METAR WIBB", "🛰️ BMKG Tactical Forecast"])

# =====================================
# TAB 1: QAM METAR (STAY ORIGINAL)
# =====================================
with tab1:
    st.title("QAM METEOROLOGICAL REPORT")
    st.subheader("Lanud Roesmin Nurjadin — WIBB")

    METAR_API = "https://aviationweather.gov/api/data/metar"
    SATELLITE_HIMA_RIAU = "http://202.90.198.22/IMAGE/HIMA/H08_RP_Riau.png"

    def fetch_metar():
        r = requests.get(METAR_API, params={"ids": "WIBB", "hours": 0}, timeout=10)
        r.raise_for_status()
        return r.text.strip()

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

    try:
        metar_text = fetch_metar()
        st.code(metar_text)
        st.divider()
        st.subheader("🛰️ Weather Satellite — Riau")
        st.image(SATELLITE_HIMA_RIAU, use_container_width=True)
    except:
        st.error("Failed to load METAR data.")

# =====================================
# TAB 2: BMKG Tactical Forecast (REFIXED)
# =====================================
with tab2:
    MS_TO_KT = 1.94384

    @st.cache_data(ttl=300)
    def fetch_forecast(code: str):
        # DETEKSI LEVEL ADM SECARA PRESISI
        # Kode dengan titik (31.75) = ADM2 (Kota/Kab)
        # Kode tanpa titik (31) = ADM1 (Provinsi)
        level = "adm2" if "." in code else "adm1"
        
        # Endpoint harus mencantumkan level di path-nya (e.g. /adm2?adm2=31.75)
        url = f"https://cuaca.bmkg.go.id/api/df/v1/forecast/{level}"
        params = {level: code}
        
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def flatten_cuaca_entry(entry):
        rows = []
        lokasi = entry.get("lokasi", {})
        for group in entry.get("cuaca", []):
            for obs in group:
                r = obs.copy()
                r.update({
                    "adm2": lokasi.get("adm2"), 
                    "kotkab": lokasi.get("kotkab"), 
                    "lon": lokasi.get("lon"), 
                    "lat": lokasi.get("lat")
                })
                r["local_datetime_dt"] = pd.to_datetime(r.get("local_datetime"))
                rows.append(r)
        df = pd.DataFrame(rows)
        for c in ["t", "hu", "ws", "tp", "wd_deg"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
        return df

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.title("🛰️ Tactical Controls")
        selected_lanud_label = st.selectbox("🎯 Target Lanud / Wilayah", options=LANUD_OPTIONS)
        selected_idx = LANUD_OPTIONS.index(selected_lanud_label)
        target_code = LANUD_LIST[selected_idx]["kode"]
        
        st.info(f"Target Sector: {target_code}")
        st.markdown("<div class='radar'></div>", unsafe_allow_html=True)
        
        show_map = st.checkbox("Show Map", value=True)
        show_table = st.checkbox("Show Table", value=False)

    st.title("Tactical Weather Operations Dashboard")
    st.markdown(f"**Deployment Area:** {selected_lanud_label}")

    with st.spinner("🛰️ Acquiring meteorological intelligence..."):
        try:
            raw_data = fetch_forecast(target_code)
            entries = raw_data.get("data", [])
            
            if not entries:
                st.warning("No operational data found for this sector.")
                st.stop()
            
            # Filter Area Spesifik
            loc_map = { (e['lokasi'].get('kotkab') or e['lokasi'].get('adm2')): e for e in entries }
            loc_choice = st.selectbox("📍 Tactical Point", options=list(loc_map.keys()))
            
            selected_entry = loc_map[loc_choice]
            df = flatten_cuaca_entry(selected_entry)
            df["ws_kt"] = df["ws"] * MS_TO_KT
            df = df.sort_values("local_datetime_dt")

            # Dashboard Metrics
            st.divider()
            now = df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("TEMP", f"{now['t']}°C")
            with c2: st.metric("HUMIDITY", f"{now['hu']}%")
            with c3: st.metric("WIND", f"{now['ws_kt']:.1f} KT")
            with c4: st.metric("RAIN", f"{now['tp']} mm")

            # Visual Trends
            st.subheader("📊 Tactical Parameter Trends")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
            fig.add_trace(go.Scatter(x=df["local_datetime_dt"], y=df["t"], name="Temp (°C)", line=dict(color='#a9df52')), 1, 1)
            fig.add_trace(go.Scatter(x=df["local_datetime_dt"], y=df["ws_kt"], name="Wind (KT)", line=dict(color='#00ffbf')), 2, 1)
            fig.update_layout(height=450, template="plotly_dark", margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

            if show_map:
                st.divider()
                st.subheader("🗺️ Tactical Map")
                m_df = pd.DataFrame({"lat": [float(selected_entry['lokasi']['lat'])], "lon": [float(selected_entry['lokasi']['lon'])]})
                st.map(m_df)

            if show_table:
                st.divider()
                st.subheader("📋 Forecast Data Log")
                st.dataframe(df)

        except Exception as e:
            st.error(f"Operational Failure: {e}")

    st.markdown("""
    <div style="text-align:center; color:#7a7; font-size:0.8rem; margin-top:50px;">
    Tactical Weather Ops Dashboard — BMKG Integrated API<br>
    Resti Maulina C.C. | STMKG Meteorologi 7C
    </div>
    """, unsafe_allow_html=True)
