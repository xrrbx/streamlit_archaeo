import streamlit as st
import folium
from streamlit_folium import folium_static
from google.cloud import bigquery
from dotenv import load_dotenv
import pandas as pd
import time

st.set_page_config(layout="wide")
st.title("⏳ Peru Archaeology Timeline Explorer")

# 1. Load Data
@st.cache_data
def load_bq_data():
    load_dotenv()
    client = bigquery.Client()
    query = """
        SELECT 
            latitude,
            longitude,
            site_name,
            material,
            cal_year,
            century_number,
            century_display
       FROM `peru-archaeology.core.fct_artifacts` 
       WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    return client.query(query).to_dataframe()

df = load_bq_data()

# Clean data boundaries
min_century = int(df['century_number'].min())
max_century = int(df['century_number'].max())

# --- FIX 1: AUTOMATED TIMELAPSE SESSION LOOP ---
# Initialize session state tracking variable for tracking automation
if 'current_time_step' not in st.session_state:
    st.session_state.current_time_step = min_century

# Layout controls
col1, col2 = st.columns([1, 4])
with col1:
    play_button = st.button("▶️ Play Timelapse")
with col2:
    stop_button = st.button("⏸️ Pause")

if play_button:
    st.session_state.playing = True
if stop_button:
    st.session_state.playing = False

# Automated progress ticker loop mechanism
if st.session_state.get('playing', False):
    if st.session_state.current_time_step < max_century:
        st.session_state.current_time_step += 1
        time.sleep(0.6) # Controls animation playback speed
        st.rerun() # Forces page refresh loop tracker
    else:
        st.session_state.playing = False # Stop automatically at the end

# Synchronize slider with our automated timeline position index
selected_century = st.slider(
    "Timeline positioning:",
    min_value=min_century,
    max_value=max_century,
    value=st.session_state.current_time_step,
    step=1
)
# Make sure manual adjustment overrides the automation baseline step tracker
st.session_state.current_time_step = selected_century

# 2. Filter Data
filtered_df = df[df['century_number'] <= selected_century]

# --- FIX 2: BULLETPROOF ERROR CHECKING FOR DISPLAY STRINGS ---
matching_century_rows = df[df['century_number'] == selected_century]

if not matching_century_rows.empty:
    current_display = matching_century_rows['century_display'].iloc[0]
else:
    # Safe fallback if this specific index gap lacks a label row
    current_display = f"Century {selected_century}" 

st.subheader(f"Showing historical distribution up to: {current_display} (Total Artifacts: {len(filtered_df)})")

# 3. Render Map Canvas
m = folium.Map(location=[-9.19, -75.01], zoom_start=5, tiles="OpenStreetMap")

for _, row in filtered_df.iterrows():
    popup_text = f"""
    <div style='font-family: Arial; font-size: 13px;'>
        <b>Site:</b> {row['site_name']}<br>
        <b>Material:</b> {row['material']}<br>
        <b>Est. Year:</b> {row['cal_year']}<br>
        <b>Era:</b> {row['century_display']}
    </div>
    """
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=5,
        color="darkred",
        fill=True,
        fill_color="red",
        fill_opacity=0.6,
        popup=folium.Popup(popup_text, max_width=250)
    ).add_to(m)

# Robust rendering mechanism
folium_static(m, width=900, height=550)
