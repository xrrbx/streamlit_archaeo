import streamlit as st
from google.cloud import bigquery
from dotenv import load_dotenv
import pandas as pd
import time

st.set_page_config(layout="wide")
st.title("⏳ Peru Archaeology Timeline Explorer")

# 1. Load Data (Executed only once on boot)
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

# Establish chronological operational boundaries
min_century = int(df['century_number'].min())
max_century = int(df['century_number'].max())

# Initialize persistent tracking variables inside global session state
if 'current_time_step' not in st.session_state:
    st.session_state.current_time_step = min_century
if 'playing' not in st.session_state:
    st.session_state.playing = False

# --- THE ISOLATION FRAGMENT CONTAINER ---
@st.fragment
def render_timelapse_map(data_frame):
    
    # 2. Control Layout Components
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.session_state.playing:
            if st.button("⏸️ Pause"):
                st.session_state.playing = False
                st.rerun(scope="fragment") # Fixed: Scopes rerun to fragment level
        else:
            if st.button("▶️ Play"):
                st.session_state.playing = True
                st.rerun(scope="fragment") # Fixed: Scopes rerun to fragment level
                
    with col2:
        # The slider widget tracks session state adjustments smoothly
        selected_century = st.slider(
            "Timeline positioning:",
            min_value=min_century,
            max_value=max_century,
            value=st.session_state.current_time_step,
            step=1,
            key="timeline_slider"
        )
    
    # Sync visual slider manual interactions back to global state tracker
    st.session_state.current_time_step = selected_century

    # 3. Process calculations on active steps
    filtered_df = data_frame[data_frame['century_number'] <= st.session_state.current_time_step]
    matching_rows = data_frame[data_frame['century_number'] == st.session_state.current_time_step]
    
    # Fixed: Fixed the text title string parser by explicitly calling the first item index location property
    if not matching_rows.empty:
        current_display = matching_rows['century_display'].iloc[0]
    else:
        current_display = f"Century {st.session_state.current_time_step}"

    st.subheader(f"Showing historical distribution up to: {current_display} (Total Artifacts: {len(filtered_df)})")

    # 4. Paint Map Elements Instantly
    if not filtered_df.empty:
        map_points = filtered_df[['latitude', 'longitude']].copy()
        st.map(map_points)
    else:
        st.warning("No data points available for this period.")

    # 5. Handle automated playback progression step increases
    if st.session_state.playing:
        if st.session_state.current_time_step < max_century:
            st.session_state.current_time_step += 1
            time.sleep(0.4) # Control frame transition pacing speed
            st.rerun(scope="fragment") # Fixed: Forces isolated looping animation lane
        else:
            st.session_state.playing = False
            st.rerun(scope="fragment")

# Run the isolated workflow structure loop
render_timelapse_map(df)
