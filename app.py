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
# 📂 DATA LANUD INDONESIA
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
    {"nama": "Sutan Sjahrir", "lokasi": "Kab. Padang Lawas Utara", "kode": "12.2"},
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
    {"nama": "Iswahjudi", "lokasi": "Kab. Magetan", "kode": "35.2"},
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

# Formatting for Selectbox
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

    def fetch_metar_history(hours=24):
        r = requests.get(METAR_API, params={"ids": "WIBB", "hours": hours}, timeout=10)
        r.raise_for_status()
        return r.text.strip().splitlines()

    def fetch_metar_ogimet(hours=24):
        end = datetime.now(timezone.utc)
        start = end - pd.Timedelta(hours=hours)
        url = "https://www.ogimet.com/display_metars2.php"
        params = {
            "lang": "en", "lugar": "WIBB", "tipo": "ALL", "ord": "REV", "nil": "NO", "fmt": "txt",
            "ano": start.year, "mes": start.month, "day": start.day, "hora": start.hour,
            "anof": end.year, "mesf": end.month, "dayf": end.day, "horaf": end.hour, "minf": end.minute
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return [l.strip() for l in r.text.splitlines() if l.startswith("WIBB")]

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

    def generate_pdf(lines):
        content = "BT\n/F1 10 Tf\n72 800 Td\n"
        for l in lines:
            safe = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            content += f"({safe}) Tj\n0 -14 Td\n"
        content += "ET"
        return (
            b"%PDF-1.4\n1 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
            b"2 0 obj<< /Length " + str(len(content)).encode() +
            b" >>stream\n" + content.encode() +
            b"\nendstream endobj\n3 0 obj<< /Type /Page /Parent 4 0 R /Contents 2 0 R "
            b"/Resources<< /Font<< /F1 1 0 R >> >> >>endobj\n4 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 "
            b"/MediaBox [0 0 595 842] >>endobj\n5 0 obj<< /Type /Catalog /Pages 4 0 R >>endobj\nxref\n0 6\n0000000000 65535 f \n"
            b"trailer<< /Size 6 /Root 5 0 R >>\n%%EOF"
        )

    now_utc = datetime.now(timezone.utc).strftime("%d %b %Y %H%M UTC")
    metar = fetch_metar()
    qam_text = [
        "METEOROLOGICAL REPORT (QAM)",
        f"DATE / TIME (UTC) : {now_utc}",
        "AERODROME         : WIBB",
        f"SURFACE WIND     : {wind(metar)}",
        f"VISIBILITY       : {visibility(metar)}",
        f"TEMP / DEWPOINT  : {temp_dew(metar)}",
        f"QNH               : {qnh(metar)}",
        "",
        "RAW METAR:",
        metar
    ]

    st.download_button("⬇️ Download QAM (PDF)", data=generate_pdf(qam_text), file_name="QAM_WIBB.pdf", mime="application/pdf")
    st.code(metar)
    st.divider()
    st.subheader("🛰️ Weather Satellite — Himawari-8 (Infrared)")
    try:
        img = requests.get(SATELLITE_HIMA_RIAU, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        st.image(img.content, use_container_width=True)
    except:
        st.warning("Satellite imagery unavailable.")

    st.divider()
    st.subheader("📊 Historical METAR Meteogram — Last 24h")
    raw = fetch_metar_history(24)
    if not raw or len(raw) < 2: raw = fetch_metar_ogimet(24)
    df_h = pd.DataFrame([parse_numeric_metar(m) for m in raw if parse_numeric_metar(m)])
    if not df_h.empty:
        df_h.sort_values("time", inplace=True)
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, subplot_titles=["Temp/Dew (°C)","Wind (kt)","QNH (hPa)","Vis (m)","Weather"])
        fig.add_trace(go.Scatter(x=df_h["time"], y=df_h["temp"], name="Temp"), 1, 1)
        fig.add_trace(go.Scatter(x=df_h["time"], y=df_h["dew"], name="Dew"), 1, 1)
        fig.add_trace(go.Scatter(x=df_h["time"], y=df_h["wind"], name="Wind"), 2, 1)
        fig.add_trace(go.Scatter(x=df_h["time"], y=df_h["qnh"], name="QNH"), 3, 1)
        fig.add_trace(go.Scatter(x=df_h["time"], y=df_h["vis"], name="Visibility"), 4, 1)
        fig.add_trace(go.Scatter(x=df_h["time"], y=df_h["RA"].astype(int), mode="markers", name="RA"), 5, 1)
        fig.add_trace(go.Scatter(x=df_h["time"], y=df_h["TS"].astype(int), mode="markers", name="TS"), 5, 1)
        fig.update_layout(height=800, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# =====================================
# TAB 2: BMKG Tactical Forecast (MODIFIED)
# =====================================
with tab2:
    API_BASE = "https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
    MS_TO_KT = 1.94384

    @st.cache_data(ttl=300)
    def fetch_forecast(code: str):
        # API BMKG /adm mendukung kode provinsi (ADM1) maupun kota (ADM2)
        params = {"adm": code} 
        resp = requests.get(API_BASE, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def flatten_cuaca_entry(entry):
        rows = []
        lokasi = entry.get("lokasi", {})
        for group in entry.get("cuaca", []):
            for obs in group:
                r = obs.copy()
                r.update({"adm2": lokasi.get("adm2"), "kotkab": lokasi.get("kotkab"), "lon": lokasi.get("lon"), "lat": lokasi.get("lat")})
                r["local_datetime_dt"] = pd.to_datetime(r.get("local_datetime"))
                rows.append(r)
        df = pd.DataFrame(rows)
        for c in ["t", "hu", "ws", "tp", "wd_deg"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
        return df

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.title("🛰️ Tactical Controls")
        
        # MODIFIKASI: Menggunakan Selectbox untuk daftar Lanud
        selected_lanud_label = st.selectbox("🎯 Target Lanud / Wilayah", options=LANUD_OPTIONS)
        
        # Mendapatkan kode dari pilihan
        selected_idx = LANUD_OPTIONS.index(selected_lanud_label)
        target_code = LANUD_LIST[selected_idx]["kode"]
        
        st.info(f"Target Code: {target_code}")
        st.markdown("<div class='radar'></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#5f5;'>Scanning Sector...</p>", unsafe_allow_html=True)
        
        show_map = st.checkbox("Show Map", value=True)
        show_table = st.checkbox("Show Table", value=False)

    st.title("Tactical Weather Operations Dashboard")
    st.markdown(f"**Target Area:** {selected_lanud_label}")

    with st.spinner("🛰️ Acquiring weather intelligence..."):
        try:
            raw = fetch_forecast(target_code)
            entries = raw.get("data", [])
            if not entries:
                st.warning("No forecast data available for this sector.")
                st.stop()
            
            # Mapping locations dalam satu ADM
            loc_map = { (e['lokasi'].get('kotkab') or e['lokasi'].get('adm2')): e for e in entries }
            loc_choice = st.selectbox("📍 Specific Area in Sector", options=list(loc_map.keys()))
            
            selected_entry = loc_map[loc_choice]
            df = flatten_cuaca_entry(selected_entry)
            df["ws_kt"] = df["ws"] * MS_TO_KT
            df = df.sort_values("local_datetime_dt")

            # Metrics
            st.divider()
            now = df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("TEMP", f"{now['t']}°C")
            with c2: st.metric("HUMIDITY", f"{now['hu']}%")
            with c3: st.metric("WIND", f"{now['ws_kt']:.1f} KT")
            with c4: st.metric("RAIN", f"{now['tp']} mm")

            # Trends
            st.subheader("📊 Parameter Trends")
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.line(df, x="local_datetime_dt", y="t", title="Temp (°C)", markers=True, color_discrete_sequence=["#a9df52"]), use_container_width=True)
                st.plotly_chart(px.line(df, x="local_datetime_dt", y="hu", title="Humidity (%)", markers=True, color_discrete_sequence=["#00ffbf"]), use_container_width=True)
            with c2:
                st.plotly_chart(px.line(df, x="local_datetime_dt", y="ws_kt", title="Wind (KT)", markers=True, color_discrete_sequence=["#00ffbf"]), use_container_width=True)
                st.plotly_chart(px.bar(df, x="local_datetime_dt", y="tp", title="Rainfall (mm)", color_discrete_sequence=["#ffbf00"]), use_container_width=True)

            if show_map:
                st.divider()
                st.subheader("🗺️ Tactical Map")
                m_df = pd.DataFrame({"lat": [float(selected_entry['lokasi']['lat'])], "lon": [float(selected_entry['lokasi']['lon'])]})
                st.map(m_df)

            if show_table:
                st.divider()
                st.subheader("📋 Forecast Data")
                st.dataframe(df)

        except Exception as e:
            st.error(f"Operational Failure: {e}")

    st.markdown("""
    <div style="text-align:center; color:#7a7; font-size:0.8rem; margin-top:50px;">
    Tactical Weather Ops Dashboard — BMKG Data © 2026<br>
    Resti Maulina C.C. | STMKG Meteorologi 7C
    </div>
    """, unsafe_allow_html=True)
