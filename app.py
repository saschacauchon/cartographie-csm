import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import numpy as np
from datetime import timedelta

# Streamlit page configuration
st.set_page_config(layout="wide")

# Load GeoJSON for France departments
geojson_url = 'https://france-geojson.gregoiredavid.fr/repo/departements.geojson'
departements_geojson = requests.get(geojson_url).json()

@st.cache_data(ttl=timedelta(days=7))
def load_data():
    # Load data from the provided URL
    clients_tessan = pd.read_csv("http://metabase.prod.tessan.cloud/public/question/84c65d1b-3c41-4725-884c-eff4e7b1a80b.csv")
    # Clean and convert Latitude and Longitude columns
    clients_tessan['Latitude'] = clients_tessan['Latitude'].str.replace(',', '.')
    clients_tessan['Longitude'] = clients_tessan['Longitude'].str.replace(',', '.')
    clients_tessan['Latitude'] = pd.to_numeric(clients_tessan['Latitude'], errors='coerce')
    clients_tessan['Longitude'] = pd.to_numeric(clients_tessan['Longitude'], errors='coerce')
    # Convert Departements column to string to avoid TypeError during sorting
    clients_tessan['Departements'] = clients_tessan['Departements'].astype(str)
    return clients_tessan

# Load the data
clients_tessan = load_data()

# Streamlit sidebar filters
st.sidebar.header("Filters")

# Extract unique years and departments for the sidebar filters
years = sorted(clients_tessan['Year'].unique())
months = sorted(clients_tessan['Month'].unique())
departments = sorted(clients_tessan['Departements'].unique())

# Department filter (single selectbox)
selected_department = st.sidebar.multiselect('Select Department', options=departments, default=departments)


# Filter the data based on the sidebar inputs
filtered_data = clients_tessan[
    (clients_tessan['Departements'].isin(selected_department))
]

filtered_data['CustomSize'] = 3

# Set the center of the map dynamically based on the selected department
if len(selected_department) == clients_tessan['Departements'].unique().shape[0]:
    map_center = {"lat": 46.603354, "lon": 1.888334}  # Center of France
    map_zoom = 5
else:
    # Calculate the mean latitude and longitude of the selected department
    dept_center = filtered_data[['Latitude', 'Longitude']].mean()
    map_center = {"lat": dept_center['Latitude'], "lon": dept_center['Longitude']}
    map_zoom = 8  # Zoom in when a department is selected

# Plot the data on a map using Plotly
fig = px.scatter_mapbox(filtered_data,
                        lat='Latitude',
                        lon='Longitude',
                        hover_name='Name',
                        hover_data={
                            #'NumberOfConsultations': True,  # Display number of consultations in hover tooltip
                            'Departements': True  # Display department in hover tooltip
                        },
                        color='Departements',  # Color points by department
                        zoom=map_zoom,  # Set dynamic zoom level
                        height=800,
                        size = 'CustomSize',
                        size_max=7  # Maximum point size
                       )

# Update layout with France GeoJSON
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=map_zoom,
    mapbox_center=map_center,  # Set the dynamic map center
    mapbox_layers=[{
        "source": departements_geojson,
        "type": "line",
        "color": "grey",
        "line": {"width": 1.5},
    }],
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    legend=dict(title="Department", itemsizing='constant')
)

# Display the Plotly map in Streamlit
st.plotly_chart(fig, use_container_width=True)

