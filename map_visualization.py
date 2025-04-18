import folium
from folium.plugins import HeatMap
import numpy as np

def create_map(center):
    """
    Create a Folium map centered at the given coordinates.
    
    Parameters:
    -----------
    center : tuple
        (latitude, longitude) of the map center
        
    Returns:
    --------
    folium.Map
        Initialized Folium map
    """
    # Create the map centered at the search center
    m = folium.Map(
        location=center,
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Add additional map layers
    folium.TileLayer(
        'https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg',
        attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name='Stamen Terrain'
    ).add_to(m)
    
    folium.TileLayer(
        'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name='CartoDB Positron'
    ).add_to(m)
    
    folium.TileLayer(
        'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name='CartoDB Dark Matter'
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

def add_last_position_marker(m, latitude, longitude):
    """
    Add a marker for the last known position of the aircraft.
    
    Parameters:
    -----------
    m : folium.Map
        The map to add the marker to
    latitude : float
        Latitude of the last known position
    longitude : float
        Longitude of the last known position
    """
    # Add a marker for the last known position
    folium.Marker(
        location=[latitude, longitude],
        popup="Last Known Position",
        tooltip="Last Known Position",
        icon=folium.Icon(color='blue', icon='plane', prefix='fa')
    ).add_to(m)

def add_search_radius(m, center, radius):
    """
    Add a circle to represent the search radius.
    
    Parameters:
    -----------
    m : folium.Map
        The map to add the circle to
    center : tuple
        (latitude, longitude) of the center of the search area
    radius : float
        Radius of the search area in nautical miles
    """
    # Convert nautical miles to meters (1 nm = 1852 meters)
    radius_meters = radius * 1852
    
    # Add a circle for the search radius
    folium.Circle(
        location=center,
        radius=radius_meters,
        color='blue',
        fill=True,
        fill_opacity=0.1,
        popup=f"Search Radius: {radius:.2f} nm"
    ).add_to(m)

def add_probability_heatmap(m, probability_points):
    """
    Add a heatmap to visualize the probability distribution of crash sites.
    
    Parameters:
    -----------
    m : folium.Map
        The map to add the heatmap to
    probability_points : list
        List of [lat, lon, probability] points representing the probability distribution
    """
    # Extract the data for the heatmap
    heatmap_data = [[point[0], point[1], point[2] * 1000] for point in probability_points]  # Scale by 1000 for better visibility
    
    # Add the heatmap layer
    HeatMap(
        heatmap_data,
        radius=15,
        max_zoom=13,
        blur=10,
        gradient={
            0.2: 'blue',
            0.4: 'lime',
            0.6: 'yellow',
            0.8: 'orange',
            1.0: 'red'
        }
    ).add_to(m)
    
    # Add markers for the highest probability points (top 5)
    sorted_points = sorted(probability_points, key=lambda x: x[2], reverse=True)
    top_points = sorted_points[:5]
    
    for i, point in enumerate(top_points):
        folium.CircleMarker(
            location=[point[0], point[1]],
            radius=8,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.8,
            popup=f"High Probability Area #{i+1}: {point[2]:.2f}"
        ).add_to(m)
