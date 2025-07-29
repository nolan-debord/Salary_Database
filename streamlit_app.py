import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
import matplotlib.pyplot as plt
import io
import base64

# -----------------------------
# Load and cache the final dataset
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/combined_affordability.csv")
    return df

df = load_data()

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filter Cities and Data")

# State filter
state_filter = st.sidebar.multiselect(
    "Select State(s)", options=sorted(df['State'].unique()), default=["TX"]
)

# City filter
city_filter = st.sidebar.multiselect(
    "Select City/Cities", options=sorted(df['City'].unique()), default=[]
)

# Real data only
only_real_data = st.sidebar.checkbox("Only Show Non-Imputed Cities", value=False)

# Salary Sliders
st.sidebar.subheader("Salary Filters")
min_salary = st.sidebar.slider("Min Data Scientist Salary", 0, 200000, 0, 5000)
min_rn_salary = st.sidebar.slider("Min RN Salary", 0, 200000, 0, 5000)
min_combined = st.sidebar.slider("Min Combined Salary", 0, 300000, 0, 5000)

# Home Value and Affordability
st.sidebar.subheader("Affordability Filters")
home_min, home_max = st.sidebar.slider("Home Value Range", 0, 1500000, (0, 1500000), 10000)
afford_min, afford_max = st.sidebar.slider("Affordability Range (Combined)", 0.0, 0.05, (0.0, 0.05), 0.001)

# Color/Value toggles
st.sidebar.header("Map Options")
color_metric = st.sidebar.selectbox(
    "Color Map Based On:",
    options=[
        "6/30/2025",
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

use_clustering = st.sidebar.checkbox("Enable Marker Clustering", value=False)

salary_toggle = st.sidebar.selectbox(
    "Salary Metric:",
    options=["A_MEAN", "A_MEDIAN", "A_PCT10", "A_PCT25", "A_PCT75", "A_PCT90"],
    format_func=lambda x: x.replace("A_", "Annual ").title()
)

# -----------------------------
# Apply Filters
# -----------------------------
filtered_df = df.copy()

if state_filter:
    filtered_df = filtered_df[filtered_df["State"].isin(state_filter)]
if city_filter:
    filtered_df = filtered_df[filtered_df["City"].isin(city_filter)]
if only_real_data:
    filtered_df = filtered_df[
        (filtered_df[f'Data Scientists_{salary_toggle}_imputed'] == False) &
        (filtered_df[f'Registered Nurses_{salary_toggle}_imputed'] == False)
    ]

filtered_df = filtered_df[
    (filtered_df[f'Data Scientists_{salary_toggle}'] >= min_salary) &
    (filtered_df[f'Registered Nurses_{salary_toggle}'] >= min_rn_salary) &
    (filtered_df['Total_Salary'] >= min_combined) &
    (filtered_df['6/30/2025'] >= home_min) & (filtered_df['6/30/2025'] <= home_max) &
    (filtered_df['Affordability_Combined'] >= afford_min) & (filtered_df['Affordability_Combined'] <= afford_max)
]

# -----------------------------
# Header
# -----------------------------
st.set_page_config(layout="wide")
st.title("🏙️ U.S. City Affordability Explorer")
st.markdown("Explore affordability for Data Scientists and RNs across U.S. cities.")

# -----------------------------
# Folium Map
# -----------------------------
st.header("📍 City Affordability Map")

folium_map = folium.Map(location=[39.8283, -98.5795], zoom_start=5)

if use_clustering:
    marker_container = MarkerCluster().add_to(folium_map)
else:
    marker_container = folium.FeatureGroup(name="Cities").add_to(folium_map)

min_val = filtered_df[color_metric].min()
max_val = filtered_df[color_metric].max()

colormap = cm.LinearColormap(
    colors=["red", "yellow", "green", "blue", "purple"],
    vmin=min_val,
    vmax=max_val
)

for _, row in filtered_df.iterrows():
    city = row['City']
    state = row['State']
    lat = row['Latitude']
    lon = row['Longitude']
    color_value = row[color_metric]

    # Generate housing chart image in memory
    fig, ax = plt.subplots()
    ax.bar(["Home Value"], [row['6/30/2025']])
    ax.set_title(f"{city} Home Value")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    img_html = f'<img src="data:image/png;base64,{encoded}" width="200">'
    plt.close(fig)

    popup_html = f"""
    <b>{city}, {state}</b><br>
    <b>DS {salary_toggle}:</b> ${row[f'Data Scientists_{salary_toggle}']:,.0f}<br>
    <b>RN {salary_toggle}:</b> ${row[f'Registered Nurses_{salary_toggle}']:,.0f}<br>
    <b>Combined:</b> ${row['Total_Salary']:,.0f}<br>
    <b>Home:</b> ${row['6/30/2025']:,.0f}<br>
    <b>Affordability:</b> {row['Affordability_Combined']:.4f}<br>
    {img_html}
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color=colormap(color_value),
        fill=True,
        fill_color=colormap(color_value),
        fill_opacity=0.85,
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"{city}, {state}"
    ).add_to(marker_container)

colormap.caption = {
    "6/30/2025": "Home Value (Lower → Higher)",
    "Total_Salary": "Combined Salary (Lower → Higher)",
    "Affordability_Combined": "Affordability (Better → Worse)",
    "Cost of Living Index": "COL Index (Lower → Higher)"
}.get(color_metric, color_metric)
colormap.add_to(folium_map)

st_folium(folium_map, width="100%", height=800)

# -----------------------------
# Table
# -----------------------------
st.header("🏆 Top Cities")
st.dataframe(
    filtered_df[[
        'City', 'State', f'Data Scientists_{salary_toggle}', f'Registered Nurses_{salary_toggle}',
        'Total_Salary', 'Affordability_Combined', 'Cost of Living Index', '6/30/2025']]
    .sort_values(by='Affordability_Combined', ascending=False)
    .reset_index(drop=True),
    use_container_width=True
)

st.markdown("---")
st.markdown("Built with ❤️ by Nolan DeBord")
