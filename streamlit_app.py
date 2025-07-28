import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# -----------------------------
# Load and cache the final dataset
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/combined_affordability.csv")  # <-- Update path if needed
    return df

# Load the data
df = load_data()

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filter Cities and Data")

default_state = "TX"

# State filter
state_filter = st.sidebar.multiselect(
    "Select State(s)", options=sorted(df['State'].unique()),
     default=[]
)

# City filter
city_filter = st.sidebar.multiselect(
    "Select City/Cities", options=sorted(df['City'].unique()), default=[]
)

if state_filter:
    df = df[df["State"].isin(state_filter)]

# Only non-imputed data
only_real_data = st.sidebar.checkbox("Only Show Non-Imputed Cities", value=False)

st.sidebar.header("Map Color Options")

color_metric = st.sidebar.selectbox(
    "Color Map Based On:",
    options=[
        "6/30/2025",  # Home value
        "Total_Salary",
        "Affordability_Combined",
        "Cost of Living Index"
    ],
    format_func=lambda x: {
        "6/30/2025": "Home Value",
        "Total_Salary": "Combined Salary",
        "Affordability_Combined": "Affordability (Combined)",
        "Cost of Living Index": "Cost of Living Index"
    }.get(x, x)
)


# Apply filters
filtered_df = df.copy()
if state_filter:
    filtered_df = filtered_df[filtered_df["State"].isin(state_filter)]
if city_filter:
    filtered_df = filtered_df[filtered_df["City"].isin(city_filter)]
if only_real_data:
    filtered_df = filtered_df[
        (filtered_df['Data Scientists_A_MEAN_imputed'] == False) &
        (filtered_df['Registered Nurses_A_MEAN_imputed'] == False)
    ]

import branca.colormap as cm

def get_color(value, colormap):
    return colormap(value)

# Define a color scale based on selected color_metric
min_val = filtered_df[color_metric].min()
max_val = filtered_df[color_metric].max()

colormap = cm.LinearColormap(
    colors=["red", "yellow", "green", "blue", "purple"],
    vmin=min_val,
    vmax=max_val
)

# -----------------------------
# Header
# -----------------------------
st.title("🏙️ U.S. City Affordability Explorer")
st.markdown("Use this interactive dashboard to explore affordability for Data Scientists and Registered Nurses across the U.S.")

# -----------------------------
# Folium Map
# -----------------------------
st.header("📍 City Affordability Map")

# Create the folium map
folium_map = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

# Create a MarkerCluster object and add it to the map
marker_cluster = MarkerCluster().add_to(folium_map)

# Loop through filtered data and add markers to the cluster
for _, row in filtered_df.iterrows():
    popup_text = f"""
    <b>{row['City']}, {row['State']}</b><br>
    <b>Combined Salary:</b> ${row['Total_Salary']:,.0f}<br>
    <b>Home Value:</b> ${row['6/30/2025']:,.0f}<br>
    <b>COST Index:</b> {row['Cost of Living Index']}<br>
    <b>Affordability:</b> {row['Affordability_Combined']:.4f}<br>
    <b>Imputed Data?</b> {'Yes' if row['Data Scientists_A_MEAN_imputed'] or row['Registered Nurses_A_MEAN_imputed'] else 'No'}
    """

    color_value = row[color_metric]

    color_value = row[color_metric]

    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=8,  # Fixed size
        color=colormap(color_value),
        fill=True,
        fill_color=colormap(color_value),
        fill_opacity=0.8,
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=f"{row['City']}, {row['State']}"
    ).add_to(marker_cluster)



colormap.caption = {
    "6/30/2025": "Home Value (Lower → Higher)",
    "Total_Salary": "Combined Salary (Lower → Higher)",
    "Affordability_Combined": "Affordability (Better → Worse)",
    "Cost of Living Index": "COL Index (Lower → Higher)"
}.get(color_metric, color_metric)

colormap.add_to(folium_map)


# Display map
st_data = st_folium(folium_map, width=1100, height=600)

# -----------------------------
# Top Cities Table
# -----------------------------
st.header("🏆 Top Cities by Combined Affordability")
st.dataframe(
    filtered_df[[
        'City', 'State', 'Data Scientists_A_MEAN', 'Registered Nurses_A_MEAN',
        'Total_Salary', 'Affordability_Combined', 'Cost of Living Index', '6/30/2025'
    ]].sort_values(by='Affordability_Combined', ascending=False).reset_index(drop=True),
    use_container_width=True
)

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown("Built with ❤️ by Nolan DeBord")
