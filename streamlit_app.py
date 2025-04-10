import streamlit as st
import pandas as pd
import math
from pathlib import Path
import plotly.express as px 
from geopy.distance import geodesic
import plotly.graph_objects as go
import requests
import json
# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='AQI Dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)

st.title("AQI Dashboard - DS 620 - Week 8")
st.text("By Huizhe Zhu, Yujie Liu, and Jitesh Gurav")
st.text("The Data has been sourced directly from the US Environmental Protection Agency Website - https://aqs.epa.gov/aqsweb/airdata/download_files.html")
st.text("    ")
# -----------------------------------------------------------------------------
# Declare some useful functions.


st.subheader("AQI Data by County - 2020 to 2024")
@st.cache_data
def get_aqi_data():
    """Grab AQI data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/AQI Data - All Years.csv'
    raw_aqi_df = pd.read_csv(DATA_FILENAME, parse_dates=["Date"])
    raw_aqi_df['Date'] = raw_aqi_df['Date'].dt.strftime('%Y-%m-%d')
    return raw_aqi_df

aqi_df = get_aqi_data()
aqi_df['Date'] = pd.to_datetime(aqi_df['Date'])
with st.sidebar:
    st.header("Filters")
    year = st.selectbox("Select Year", sorted(aqi_df['Date'].dt.year.unique()))
    day = st.date_input("Pick a Day", aqi_df['Date'].min())

# Filter data
filtered_df = aqi_df[aqi_df['Date'].dt.year == year]

# If specific day selected
if day:
    filtered_df = aqi_df[aqi_df['Date'] == pd.to_datetime(day)]
    animation = False
else:
    animation = True

# Plot
fig = px.choropleth(
    aqi_df,
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    locations="FIPS",
    color="AQI",
    color_continuous_scale="RdYlGn_r",  # red = bad, green = good
    range_color=(0, 500),  # AQI scale typically goes 0–500
    scope="usa",
    labels={'AQI': 'AQI'},
    animation_frame="Date",  # Animates over time
)

fig.update_layout(
    title_text='Daily AQI by US County (2020–2024)',
    geo=dict(lakecolor='rgb(255, 255, 255)')
)
fig.update_layout(
    margin={"r":0,"t":30,"l":0,"b":0},
    title="Air Quality Index (AQI) by County"
)

st.plotly_chart(fig, use_container_width=True)

st.text("    ")
st.text("    ")

st.subheader("AQI Data for NY City")
aqi_df['FIPS'] = aqi_df['FIPS'].astype(str)
nyc_fips = ['36061', '36047', '36081', '36005', '36085']
ny_df = aqi_df[aqi_df['FIPS'].isin(nyc_fips)].copy()
#ny_df = aqi_df[aqi_df['FIPS'].str.startswith("36")].copy()

# Make sure fips is string and has 5 digits
ny_df['FIPS'] = ny_df['FIPS'].apply(lambda x: f"{int(x):05d}")

# Plotly choropleth
fig = px.choropleth(
    ny_df,
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    locations="FIPS",
    color="AQI",
    color_continuous_scale="RdYlGn_r",
    range_color=(0, 500),
    scope="usa",
    labels={'AQI': 'AQI'},animation_frame="Date"
)

# Zoom into NY by restricting to NY counties
fig.update_geos(fitbounds="locations", visible=False)

fig.update_layout(
    title="Air Quality Index (AQI) – New York City",
    margin={"r":0,"t":30,"l":0,"b":0}
)

st.plotly_chart(fig, use_container_width=True)


st.text("    ")
st.text("    ")

@st.cache_data
def load_data():
    DATA_FILENAME = Path(__file__).parent/'data/AQI Data - All Years.csv'
    df = pd.read_csv(DATA_FILENAME, parse_dates=["Date"])
    df['FIPS'] = df['FIPS'].apply(lambda x: f"{int(x):05d}")
    
    # NYC boroughs and corresponding FIPS
    borough_map = {
        'Manhattan': '36061',
        'Brooklyn': '36047',
        'Queens': '36081',
        'The Bronx': '36005',
        'Staten Island': '36085'
    }

    borough_map_rev = {
        '36061':'Manhattan',
        '36047':'Brooklyn',
        '36081':'Queens',
        '36005':'The Bronx',
        '36085':'Staten Island'
    }

    df['borough'] = df['FIPS'].map(borough_map_rev)    
    # df['FIPS'] = df['FIPS'].map({v: k for k, v in borough_map.items()})
    nyc_df = df[df['borough'].notna()].copy()
    return nyc_df, borough_map

df, borough_map = load_data()
print(df)


st.subheader("NYC Air Quality Index (AQI) Over Time")
st.markdown("Visualize AQI trends by borough from your dataset.")

selected_borough = st.selectbox("Choose a borough", list(borough_map.keys()))

filtered = df[df['borough'] == selected_borough]

fig = px.line(
    filtered,
    x="Date",
    y="AQI",
    title=f"AQI Over Time – {selected_borough}",
    labels={"aqi": "Air Quality Index", "Date": "Date"},
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)


st.text("   ")
st.text("   ")

def load_data():
    DATA_FILENAME = Path(__file__).parent/'data/AQI Data - All Years.csv'
    df = pd.read_csv(DATA_FILENAME, parse_dates=["Date"])
    
    # Ensure FIPS are 5 digits
    df['FIPS'] = df['FIPS'].apply(lambda x: f"{int(x):05d}")
    
    # Load CSV for U.S. counties with FIPS codes and lat/lng
    latlng_df = pd.read_csv("https://gist.githubusercontent.com/russellsamora/12be4f9f574e92413ea3f92ce1bc58e6/raw/3f18230058afd7431a5d394dab7eeb0aafd29d81/us_county_latlng.csv")
    
    # Ensure FIPS are 5 digits
    latlng_df['fips_code'] = latlng_df['fips_code'].apply(lambda x: f"{int(x):05d}")
    
    return df, latlng_df

df, latlng_df = load_data()

# --------------------------
# User Input (AQI threshold & Distance threshold)
# --------------------------

st.subheader("Find Nearby Counties with Good Air Quality (AQI < Threshold)")

# AQI threshold input
aqi_threshold = st.number_input("Enter AQI Threshold", min_value=0, max_value=500, value=30)

# Distance threshold input (in kilometers)
distance_threshold = st.number_input("Enter Distance Threshold (km)", min_value=0, value=50)

# --------------------------
# Define NYC Coordinates
# --------------------------

nyc_coords = {'latitude': 40.7128, 'longitude': -74.0060}

# --------------------------
# Filter Counties by AQI < Threshold and Distance
# --------------------------

# Filter counties with AQI < the user-specified threshold
filtered_aqi_df = df.loc[df['AQI'] < aqi_threshold]
filtered_aqi_df.reset_index(drop = True, inplace = True)

# Merge AQI data with lat/lng data using FIPS code
merged_df = pd.merge(filtered_aqi_df, latlng_df, left_on="FIPS", right_on="fips_code")
merged_df.reset_index(drop = True, inplace = True)

# Function to calculate the distance between NYC and each county using lat/lng
def calculate_distance(row):
    county_coords = (row['lat'], row['lng'])
    return geodesic((nyc_coords['latitude'], nyc_coords['longitude']), county_coords).km

# Add distance column to the merged DataFrame
merged_df['distance_km'] = merged_df.apply(calculate_distance, axis=1)

# Filter for counties within the specified distance threshold
nearby_counties_df = merged_df[merged_df['distance_km'] <= distance_threshold]

# --------------------------
# Plotting with Plotly
# --------------------------

# Plot map
min_lat = nearby_counties_df['lat'].min() - 5 # Small margin for better visualization
max_lat = nearby_counties_df['lat'].max() + 5
min_lng = nearby_counties_df['lng'].min() - 5
max_lng = nearby_counties_df['lng'].max() + 5

# --------------------------
# Plotting with Plotly
# --------------------------

# Plot map
if not nearby_counties_df.empty:
    fig = go.Figure()

    # Plot New York City
    fig.add_trace(go.Scattergeo(
        lon=[nyc_coords['longitude']],
        lat=[nyc_coords['latitude']],
        text="New York City",
        marker=dict(color="blue", size=10),
        name="New York City"
    ))

    # Plot nearby counties with AQI < threshold
    fig.add_trace(go.Scattergeo(
        lon=nearby_counties_df['lng'],
        lat=nearby_counties_df['lat'],
        text=nearby_counties_df['FIPS'] + " - AQI: " + nearby_counties_df['AQI'].astype(str),
        marker=dict(color=nearby_counties_df['AQI'], colorscale="Viridis", size=10, colorbar=dict(title="AQI")),
        name="Nearby Counties with AQI < {aqi_threshold}"
    ))

    # Update the map's visible region to fit the counties within the distance threshold
    fig.update_geos(
        visible=False,
        scope="usa",
        showland=True,
        landcolor="lightgray",center=dict(lat=nyc_coords['latitude'], lon=nyc_coords['longitude']),
        projection_type="albers usa",
        lonaxis=dict(range=[min_lng, max_lng]),  # Set longitude range
        lataxis=dict(range=[min_lat, max_lat])   # Set latitude range
    )

    fig.update_layout(
        title=f"Counties within {distance_threshold} km of NYC with AQI < {aqi_threshold}",
    )

    st.plotly_chart(fig)

else:
    st.write(f"No counties found within {distance_threshold} km of NYC with AQI below {aqi_threshold}.")
