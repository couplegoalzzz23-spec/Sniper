import streamlit as st

# Set page config di awal
st.set_page_config(page_title="Tactical Weather Ops — BMKG", layout="wide")

import requests
import re
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import plotly.express as px

# =====================================
# LOAD DATA LANUD (HARDCODED FOR VALIDATION)
# =====================================
@st.cache_data
def load_lanud_codes():
    # Data divalidasi berdasarkan Kode Wilayah BPS (ADM2 untuk Kota/Kab)
    data = [
        ["Lanud Halim Perdanakusuma", "31.75", "Jakarta Timur"],
        ["Lanud Atang Sendjaja", "32.71", "Kota Bogor"],
        ["Lanud Suryadarma", "32.13", "Subang"],
        ["Lanud Husein Sastranegara", "32.73", "Kota Bandung"],
        ["Lanud Sulaiman", "32.04", "Kab. Bandung"],
        ["Lanud Wiriadinata", "32.78", "Kota Tasikmalaya"],
        ["Lanud Sugiri Sukani", "32.10", "Majalengka"],
        ["Lanud Roesmin Nurjadin", "14.71", "Pekanbaru"],
        ["Lanud Soewondo", "12.71", "Medan"],
        ["Lanud Sultan Iskandar Muda", "11.06", "Aceh Besar"],
        ["Lanud Maimun Saleh", "11.72", "Sabang"],
        ["Lanud Sutan Sjahrir", "13.71", "Padang"],
        ["Lanud Raja Haji Fisabilillah", "21.72", "Tanjung Pinang"],
        ["Lanud Hang Nadim", "21.71", "Batam"],
        ["Lanud H. AS Hanandjoeddin", "19.02", "Belitung"],
        ["Lanud Sri Mulyono Herlambang", "16.71", "Palembang"],
        ["Lanud Pangeran M. Bun Yamin", "18.05", "Tulang Bawang"],
        ["Lanud Supadio", "61.12", "Kubu Raya"],
        ["Lanud Harry Hadisoemantri", "61.07", "Bengkayang"],
        ["Lanud Iskandar", "62.01", "Kotawaringin Barat"],
        ["Lanud Syamsudin Noor", "63.72", "Banjarbaru"],
        ["Lanud Dhomber", "64.71", "Balikpapan"],
        ["Lanud Anang Busra", "65.71", "Tarakan"],
        ["Lanud Abdulrachman Saleh", "35.07", "Kab. Malang"],
        ["Lanud Iswahjudi", "35.20", "Magetan"],
        ["Lanud Adi Soemarmo", "33.09", "Boyolali"],
        ["Lanud Adisutjipto", "34.04", "Sleman"],
        ["Lanud Jenderal Besar Soedirman", "33.03", "Purbalingga"],
        ["Lanud Muljono", "35.15", "Sidoarjo"],
        ["Lanud El Tari", "53.71", "Kota Kupang"],
        ["Lanud I Gusti Ngurah Rai", "51.03", "Badung"],
        ["Lanud Zainuddin Abdul Madjid", "52.02", "Lombok Tengah"],
        ["Lanud Sultan Hasanuddin", "73.09", "Maros"],
        ["Lanud Haluoleo", "74.05", "Konawe Selatan"],
        ["Lanud Sam Ratulangi", "71.71", "Manado"],
        ["Lanud Pattimura", "81.71", "Ambon"],
        ["Lanud Leo Wattimena", "82.07", "Pulau Morotai"],
        ["Lanud Silas Papare", "91.03", "Kab. Jayapura"],
        ["Lanud Manuhua", "91.06", "Biak Numfor"],
        ["Lanud Yohanis Kapiyau", "91.09", "Mimika"],
        ["Lanud Johannes Abraham Dimara", "91.01", "Merauke"]
    ]
    df = pd.DataFrame(data, columns=["Nama Lanud", "Kode Wilayah", "Lokasi"])
    return df

lanud_df = load_lanud_codes()

# =====================================
# CSS
# =====================================
st.markdown("""
<style>
body {background-color: #0b0c0c; color: #cfd2c3; font-family: Consolas;}
h1, h2, h3, h4 {color: #a9df52;}
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
        try:
            r = requests.get(METAR_API, params={"ids": "WIBB", "hours": 0}, timeout=10)
            r.raise_for_status()
            return r.text.strip()
        except:
            return "METAR Data Unavailable"

    st.code(fetch_metar())

# =====================================
# TAB 2
# =====================================
with tab2:
    MS_TO_KT = 1.94384

    @st.cache_data(ttl=300)
    def fetch_forecast(kode):
        # Penentuan level API secara otomatis (adm1 atau adm2)
        level = "adm2" if "." in kode else "adm1"
        url = f"https://cuaca.bmkg.go.id/api/df/v1/forecast/{level}"
        
        r = requests.get(url, params={level: kode}, timeout=15)
        r.raise_for_status()
        return r.json()

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

    # SIDEBAR
    with st.sidebar:
        st.title("🛰️ Tactical Controls")
        selected_lanud = st.selectbox("✈️ Select Indonesian Air Base", lanud_df["Nama Lanud"])
        
        row = lanud_df[lanud_df["Nama Lanud"] == selected_lanud].iloc[0]
        target_code = row["Kode Wilayah"]

        st.info(f"**Lanud:** {row['Nama Lanud']}\n\n**Lokasi:** {row['Lokasi']}\n\n**Kode Wilayah:** {target_code}")
        st.markdown("<div class='radar'></div>", unsafe_allow_html=True)
        show_map = st.checkbox("Show Map", True)
        show_table = st.checkbox("Show Table", False)

    st.title("Tactical Weather Operations Dashboard")

    try:
        raw = fetch_forecast(target_code)
        entries = raw.get("data", [])

        if not entries:
            st.warning("No data available for this sector.")
            st.stop()

        mapping = {}
        for e in entries:
            lok = e.get("lokasi", {})
            label = lok.get("kotkab") or lok.get("adm2") or "Unknown Area"
            mapping[label] = e

        loc_choice = st.selectbox("🎯 Select Tactical Point", list(mapping.keys()))
        df = flatten(mapping[loc_choice])

        if df.empty:
            st.warning("Empty dataset received.")
            st.stop()

        df["ws_kt"] = df["ws"] * MS_TO_KT
        now = df.iloc[0]

        st.subheader(f"⚡ Tactical Status: {loc_choice}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TEMP", f"{now['t']}°C")
        c2.metric("HUMIDITY", f"{now['hu']}%")
        c3.metric("WIND", f"{now['ws_kt']:.1f} KT")
        c4.metric("RAIN", f"{now['tp']} mm")

        st.subheader("📊 Trends")
        fig_temp = px.line(df, x="local_datetime_dt", y="t", title="Temperature Trend (°C)")
        fig_temp.update_traces(line_color='#a9df52')
        st.plotly_chart(fig_temp, use_container_width=True)

        fig_wind = px.line(df, x="local_datetime_dt", y="ws_kt", title="Wind Speed Trend (KT)")
        fig_wind.update_traces(line_color='#33ff55')
        st.plotly_chart(fig_wind, use_container_width=True)

        if show_map:
            st.subheader("🗺️ Tactical Map")
            st.map(pd.DataFrame({
                "lat": [float(df.iloc[0]["lat"])],
                "lon": [float(df.iloc[0]["lon"])]
            }))

        if show_table:
            st.subheader("📋 Data Log")
            st.dataframe(df)

        st.download_button(
            "⬇️ Download Intelligence Report (CSV)",
            df.to_csv(index=False),
            file_name=f"Tactical_{selected_lanud}_{datetime.now().strftime('%Y%m%d')}.csv"
        )

    except Exception as e:
        st.error(f"Tactical Error: {e}")

    st.markdown("""
    ---
    <div style="text-align:center;color:#7a7;font-size:0.8em;">
    Tactical Weather Ops Dashboard — BMKG API Integrated<br>
    Resti Maulina C.C. | STMKG Meteorologi 7C
    </div>
    """, unsafe_allow_html=True)
