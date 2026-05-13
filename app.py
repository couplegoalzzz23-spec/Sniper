import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ==============================

# PAGE CONFIG

# ==============================

st.set_page_config(
page_title="Tactical Weather Ops Dashboard",
layout="wide"
)

# ==============================

# ICAO LANUD DATABASE

# ==============================

LANUD_ICAO = {
"WIHH": {"lanud": "Halim Perdanakusuma", "adm1": "31"},
"WIII": {"lanud": "Soekarno-Hatta", "adm1": "36"},
"WICC": {"lanud": "Husein Sastranegara", "adm1": "32"},
"WAHP": {"lanud": "Iswahjudi", "adm1": "35"},
"WADD": {"lanud": "Ngurah Rai", "adm1": "51"},
"WAAA": {"lanud": "Sultan Hasanuddin", "adm1": "73"},
}

API_BASE = "https://cuaca.bmkg.go.id/api/df/v1/forecast/adm"
MS_TO_KT = 1.94384

# ==============================

# FETCH DATA

# ==============================

@st.cache_data(ttl=300)
def fetch_forecast(adm1):
response = requests.get(API_BASE, params={"adm1": adm1}, timeout=15)
response.raise_for_status()
return response.json()

def flatten(entry):
rows = []
lokasi = entry.get("lokasi", {})

```
for group in entry.get("cuaca", []):
    for obs in group:
        row = obs.copy()
        row.update({
            "provinsi": lokasi.get("provinsi"),
            "kotkab": lokasi.get("kotkab"),
            "lat": lokasi.get("lat"),
            "lon": lokasi.get("lon")
        })
        rows.append(row)

df = pd.DataFrame(rows)

if "ws" in df.columns:
    df["ws_kt"] = pd.to_numeric(df["ws"], errors="coerce") * MS_TO_KT

return df
```

# ==============================

# SIDEBAR

# ==============================

with st.sidebar:
st.title("🛰 Tactical Controls")

```
selected_icao = st.selectbox(
    "Select ICAO / Lanud",
    list(LANUD_ICAO.keys())
)

selected = LANUD_ICAO[selected_icao]
adm1 = selected["adm1"]

st.success(f"{selected_icao} — {selected['lanud']}")

show_table = st.checkbox("Show Raw Table", False)
show_map = st.checkbox("Show Map", True)
```

# ==============================

# MAIN DASHBOARD

# ==============================

st.title("✈ Tactical Weather Operations Dashboard")
st.caption("BMKG Forecast API + ICAO Lanud Indonesia")

try:
raw = fetch_forecast(adm1)

```
entries = raw.get("data", [])

if not entries:
    st.warning("No forecast data available")
    st.stop()

entry = entries[0]
df = flatten(entry)

if df.empty:
    st.warning("No weather observations found")
    st.stop()

now = df.iloc[0]

# ==============================
# METRICS
# ==============================
c1, c2, c3, c4 = st.columns(4)

c1.metric("Temperature", f"{now.get('t', '—')} °C")
c2.metric("Wind", f"{now.get('ws_kt', 0):.1f} KT")
c3.metric("Visibility", f"{now.get('vs', '—')} m")
c4.metric("Weather", now.get("weather_desc", "—"))

st.divider()

# ==============================
# TEMPERATURE TREND
# ==============================
if "t" in df.columns:
    fig_temp = px.line(
        df,
        y="t",
        title="Temperature Trend"
    )
    st.plotly_chart(fig_temp, use_container_width=True)

# ==============================
# WIND TREND
# ==============================
if "ws_kt" in df.columns:
    fig_wind = px.line(
        df,
        y="ws_kt",
        title="Wind Speed Trend"
    )
    st.plotly_chart(fig_wind, use_container_width=True)

st.divider()

# ==============================
# SATELLITE
# ==============================
st.subheader("🛰 BMKG Satellite")

st.image(
    "https://inderaja.bmkg.go.id/IMAGE/HIMA/H08_EH_Indonesia.png",
    use_container_width=True
)

# ==============================
# RADAR
# ==============================
st.subheader("🌧 BMKG Radar")

components.iframe(
    "https://inderaja.bmkg.go.id/Radar",
    height=500
)

# ==============================
# MAP
# ==============================
if show_map:
    try:
        lat = float(entry["lokasi"]["lat"])
        lon = float(entry["lokasi"]["lon"])

        st.subheader("🗺 Location")

        st.map(
            pd.DataFrame({
                "lat": [lat],
                "lon": [lon]
            })
        )
    except Exception:
        st.warning("Map unavailable")

# ==============================
# RAW TABLE
# ==============================
if show_table:
    st.subheader("📋 Raw Forecast Data")
    st.dataframe(df)

# ==============================
# EXPORT CSV
# ==============================
csv = df.to_csv(index=False)

st.download_button(
    label="⬇ Download CSV",
    data=csv,
    file_name=f"{selected_icao}_forecast.csv",
    mime="text/csv"
)
```

except Exception as e:
st.error(f"Error: {str(e)}")

st.divider()
st.caption("Tactical Weather Ops Dashboard — ICAO Military Edition")
