import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# -----------------------------
# Load and cache the final dataset
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/merged_final_dataset.csv")  # <-- Update path if needed
    return df

# Load the data
df = load_data()

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filter Cities and Data")

# State filter
state_filter = st.sidebar.multiselect(
    "Select State(s)", options=sorted(df['State'].unique()), default=[]
)

# City filter
city_filter = st.sidebar.multiselect(
    "Select City/Cities", options=sorted(df['City'].unique()), default=[]
)

# Only non-imputed data
only_real_data = st.sidebar.checkbox("Only Show Non-Imputed Cities", value=False)

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
m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

# Add city points to the map
for _, row in filtered_df.iterrows():
    popup_text = (
        f"<b>{row['City']}, {row['State']}</b><br>"
        f"Data Scientist Salary: ${row['Data Scientists_A_MEAN']:,.0f}<br>"
        f"RN Salary: ${row['Registered Nurses_A_MEAN']:,.0f}<br>"
        f"Affordability (Combined): {row['Affordability_Combined']:.4f}"
    )
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=5,
        color='blue',
        fill=True,
        fill_opacity=0.6,
        popup=popup_text
    ).add_to(m)

# Display map
st_data = st_folium(m, width=900, height=600)

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
