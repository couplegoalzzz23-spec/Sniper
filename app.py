```python
import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import streamlit.components.v1 as components
from PIL import Image
from io import BytesIO

# =====================================
# ⚙️ KONFIGURASI DASAR
# =====================================
st.set_page_config(page_title="Tactical Weather Ops — BMKG ICAO", layout="wide")

# =====================================
# ✈ DATABASE ICAO LANUD INDONESIA
# =====================================
LANUD_ICAO = {
    "WIHH":{"lanud":"Halim Perdanakusuma","adm1":"31"},
    "WIII":{"lanud":"Soekarno-Hatta","adm1":"36"},
    "WICC":{"lanud":"Husein Sastranegara","adm1":"32"},
    "WAHS":{"lanud":"Adi Soemarmo","adm1":"33"},
    "WAHH":{"lanud":"Adisutjipto","adm1":"34"},
    "WARJ":{"lanud":"Juanda","adm1":"35"},
    "WARI":{"lanud":"Abdulrachman Saleh","adm1":"35"},
    "WAHP":{"lanud":"Iswahjudi","adm1":"35"},
    "WAAA":{"lanud":"Sultan Hasanuddin","adm1":"73"},
    "WADD":{"lanud":"Ngurah Rai","adm1":"51"},
    "WAJJ":{"lanud":"Sentani","adm1":"91"},
    "WAPP":{"lanud":"Pattimura","adm1":"81"},
    "WIMM":{"lanud":"Soewondo","adm1":"12"},
    "WIPT":{"lanud":"Roesmin Nurjadin","adm1":"14"},
    "WIPP":{"lanud":"Sultan Mahmud Badaruddin II","adm1":"16"},
    "WIOO":{"lanud":"Supadio","adm1":"61"},
    "WAMM":{"lanud":"Sam Ratulangi","adm1":"71"},
    "WATO":{"lanud":"El Tari","adm1":"53"}
}

# =====================================
# CSS
# =====================================
st.markdown("""
<style>
body {
    background-color: #0b0c0c;
    color: #cfd2c3;
}
.flight-card {
    padding: 20px;
    background-color: #0f1111;
    border: 1px solid #2b3c2b;
    border-radius: 10px;
    margin-bottom: 20px;
}
.flight-title {
    color: #a9df52;
    font-size: 1.3rem;
    font-weight: bold;
}
.metric-value {
    font-size: 2rem;
    color: #b6ff6d;
}
.radar {
  width:160px;
  height:160px;
  border-radius:50%;
  border:2px solid #33ff55;
  margin:auto;
  box-shadow:0 0 20px #33ff55;
}
</style>
""", unsafe_allow_html=True)

# =====================================
# API
# =====================================
API_BASE = "https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
MS_TO_KT = 1.94384

# =====================================
# UTIL
# =====================================
@st.cache_data(ttl=300)
def fetch_forecast(adm1):
    r = requests.get(API_BASE, params={"adm1": adm1}, timeout=10)
    r.raise_for_status()
    return r.json()

def flatten(entry):
    rows=[]
    lokasi=entry.get("lokasi",{})
    for group in entry.get("cuaca",[]):
        for obs in group:
            x=obs.copy()
            x.update({
                "provinsi":lokasi.get("provinsi"),
                "kotkab":lokasi.get("kotkab"),
                "lat":lokasi.get("lat"),
                "lon":lokasi.get("lon")
            })
            rows.append(x)
    df=pd.DataFrame(rows)
    if "ws" in df.columns:
        df["ws_kt"]=pd.to_numeric(df["ws"],errors="coerce")*MS_TO_KT
    return df

# =====================================
# SIDEBAR
# =====================================
with st.sidebar:
    st.title("🛰 Tactical Controls")

    selected_icao = st.selectbox(
        "Select ICAO / Lanud",
        list(LANUD_ICAO.keys())
    )

    lanud = LANUD_ICAO[selected_icao]
    adm1 = lanud["adm1"]
    icao_code = selected_icao

    st.success(f"{icao_code} — {lanud['lanud']}")

    st.markdown("<div class='radar'></div>", unsafe_allow_html=True)

    show_map = st.checkbox("Show Map", True)
    show_table = st.checkbox("Show Table", False)

# =====================================
# MAIN
# =====================================
st.title("✈ Tactical Weather Operations Dashboard")
st.caption("BMKG Live Forecast + ICAO Lanud Mapping")

try:
    raw = fetch_forecast(adm1)
    entries = raw.get("data",[])

    if not entries:
        st.warning("No data")
        st.stop()

    entry = entries[0]
    df = flatten(entry)

    now = df.iloc[0]

    st.markdown("<div class='flight-card'>", unsafe_allow_html=True)
    st.markdown("<div class='flight-title'>Key Weather Status</div>", unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)

    c1.metric("Temp °C", now.get("t","—"))
    c2.metric("Wind KT", f"{now.get('ws_kt',0):.1f}")
    c3.metric("Visibility", now.get("vs","—"))
    c4.metric("Weather", now.get("weather_desc","—"))

    st.markdown("</div>", unsafe_allow_html=True)

    # Trend
    st.subheader("📈 Weather Trends")

    if "t" in df.columns:
        st.plotly_chart(
            px.line(df,y="t",title="Temperature"),
            use_container_width=True
        )

    if "ws_kt" in df.columns:
        st.plotly_chart(
            px.line(df,y="ws_kt",title="Wind Speed"),
            use_container_width=True
        )

    # Satellite
    st.subheader("🛰 Satellite")
    st.image(
        "https://inderaja.bmkg.go.id/IMAGE/HIMA/H08_EH_Indonesia.png",
        use_container_width=True
    )

    # Radar
    st.subheader("🌧 Radar")
    components.iframe(
        "https://inderaja.bmkg.go.id/Radar",
        height=500
    )

    # Map
    if show_map:
        try:
            lat=float(entry["lokasi"]["lat"])
            lon=float(entry["lokasi"]["lon"])
            st.map(pd.DataFrame({"lat":[lat],"lon":[lon]}))
        except:
            pass

    # Table
    if show_table:
        st.dataframe(df)

    # Export
    st.subheader("💾 Export")
    csv=df.to_csv(index=False)

    st.download_button(
        "Download CSV",
        csv,
        file_name=f"{icao_code}.csv"
    )

except Exception as e:
    st.error(f"Error: {e}")

st.markdown("""
---
<center>
Tactical Weather Ops Dashboard — ICAO Military Edition
</center>
""", unsafe_allow_html=True)
```
