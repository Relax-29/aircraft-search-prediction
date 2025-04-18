import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import pandas as pd
import numpy as np
import csv
import io
from datetime import datetime
import streamlit.components.v1 as components
import os
from serve_frontend import serve_tracker_frontend

from aircraft_data import aircraft_types, get_aircraft_specs
from search_algorithm import calculate_search_area, calculate_probability_distribution
from map_visualization import create_map, add_last_position_marker, add_probability_heatmap, add_search_radius
from utils import haversine_distance, calculate_bearing, export_search_coordinates
from database_view import show_database_view

# Set page configuration
st.set_page_config(
    page_title="Aircraft Search Location Calculator",
    page_icon="✈️",
    layout="wide"
)

# Check if we should serve the aircraft tracker frontend directly
serve_tracker_frontend()

# Add interface selector to the sidebar
st.sidebar.header("Interface Options")
interface_option = st.sidebar.radio(
    "Select Interface",
    ["Streamlit Interactive", "HTML/JavaScript Version", "Aircraft Tracker (Real-time)", "Database Records"]
)

# Check which interface to show
if interface_option == "HTML/JavaScript Version":
    # Remove padding and margins for HTML view
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 0;
            padding-bottom: 0;
            padding-left: 0;
            padding-right: 0;
            max-width: 100%;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Display explanation
    st.info("This is the HTML/JavaScript version of the calculator. It provides the same functionality but with a different user interface.")
    
    # Load and display the HTML interface
    try:
        with open('static/index.html', 'r') as f:
            html_content = f.read()
            
        # Inject base path for resources
        html_content = html_content.replace('src="js/', 'src="static/js/')
        html_content = html_content.replace('href="css/', 'href="static/css/')
            
        # Display the HTML content in an iframe
        components.html(html_content, height=900, scrolling=True)
    except Exception as e:
        st.error(f"Error loading HTML interface: {str(e)}")
        st.info("Please make sure the static/index.html file exists.")
        
elif interface_option == "Aircraft Tracker (Real-time)":
    # Remove padding and margins for HTML view
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 0;
            padding-bottom: 0;
            padding-left: 0;
            padding-right: 0;
            max-width: 100%;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Display explanation
    st.info("This is the advanced Aircraft Tracker with real-time tracking capabilities using the OpenSky Network API and includes emergency landing prediction features.")
    
    # Load and display the aircraft tracker interface
    try:
        with open('aircraft-tracker/index.html', 'r') as f:
            html_content = f.read()
            
        # Inject base path for resources to ensure they load correctly in Streamlit
        html_content = html_content.replace('src="js/', 'src="aircraft-tracker/js/')
        html_content = html_content.replace('href="css/', 'href="aircraft-tracker/css/')
            
        # Display the HTML content in an iframe
        components.html(html_content, height=900, scrolling=True)
    except Exception as e:
        st.error(f"Error loading Aircraft Tracker interface: {str(e)}")
        st.info("Please make sure the aircraft-tracker/index.html file exists.")

elif interface_option == "Database Records":
    # Show the database view interface
    show_database_view()
        
else:
    # Original Streamlit Interface
    # Title and description
    st.title("Aircraft Search Location Calculator")
    st.markdown("""
    This tool helps emergency responders determine the most probable search area for a missing aircraft
    based on its last known position and flight parameters. The calculation takes into account aircraft specifications,
    weather conditions, and flight characteristics to generate a probability heatmap of potential crash sites.
    """)

    # Sidebar for inputs
    st.sidebar.header("Last Known Aircraft Parameters")

    # Aircraft type
    aircraft_type = st.sidebar.selectbox(
        "Aircraft Type",
        options=list(aircraft_types.keys()),
        help="Select the type of aircraft that is missing"
    )

    # Last known position
    st.sidebar.subheader("Last Known Position")
    latitude = st.sidebar.number_input("Latitude (degrees)", value=37.7749, min_value=-90.0, max_value=90.0, 
                                      help="Last known latitude in decimal degrees (e.g., 37.7749)")
    longitude = st.sidebar.number_input("Longitude (degrees)", value=-122.4194, min_value=-180.0, max_value=180.0,
                                       help="Last known longitude in decimal degrees (e.g., -122.4194)")
    altitude = st.sidebar.number_input("Altitude (feet)", value=30000, min_value=0, max_value=60000,
                                      help="Last known altitude in feet above sea level")

    # Flight parameters
    st.sidebar.subheader("Flight Parameters")
    ground_speed = st.sidebar.number_input("Ground Speed (knots)", value=450, min_value=0, max_value=1000,
                                          help="Last known ground speed in knots")
    heading = st.sidebar.number_input("Heading (degrees)", value=90.0, min_value=0.0, max_value=360.0,
                                     help="Last known heading in degrees (0-360, where 0 is North)")
    vertical_speed = st.sidebar.number_input("Vertical Speed (feet/min)", value=0, min_value=-8000, max_value=8000,
                                            help="Last known vertical speed in feet per minute (negative for descent)")

    # Environmental conditions
    st.sidebar.subheader("Environmental Conditions")
    wind_speed = st.sidebar.number_input("Wind Speed (knots)", value=15, min_value=0, max_value=200,
                                        help="Current wind speed in knots")
    wind_direction = st.sidebar.number_input("Wind Direction (degrees)", value=270.0, min_value=0.0, max_value=360.0,
                                            help="Wind direction in degrees (0-360, where 0 is North)")
    visibility = st.sidebar.selectbox(
        "Visibility Conditions",
        options=["Excellent", "Good", "Moderate", "Poor", "Very Poor"],
        index=1,
        help="Current visibility conditions in the search area"
    )

    # Search parameters
    st.sidebar.subheader("Search Parameters")
    search_radius_multiplier = st.sidebar.slider(
        "Search Radius Factor",
        min_value=1.0,
        max_value=5.0,
        value=2.0,
        step=0.1,
        help="Multiplier to increase the search radius beyond the calculated minimum (larger values cover more area)"
    )
    num_points = st.sidebar.slider(
        "Probability Points",
        min_value=100,
        max_value=5000,
        value=1000,
        step=100,
        help="Number of points to generate in the probability distribution (higher values give more detail but take longer)"
    )

    # Get aircraft specifications
    aircraft_specs = get_aircraft_specs(aircraft_type)

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        # Calculate search area
        if st.button("Calculate Search Area"):
            with st.spinner("Calculating probable search area..."):
                # Get the search radius and center point
                search_center, search_radius, glide_distance = calculate_search_area(
                    latitude,
                    longitude,
                    altitude,
                    ground_speed,
                    heading,
                    vertical_speed,
                    wind_speed,
                    wind_direction,
                    aircraft_specs,
                    search_radius_multiplier
                )
                
                # Generate probability distribution for the search area
                probability_points = calculate_probability_distribution(
                    search_center,
                    search_radius,
                    num_points,
                    heading,
                    wind_direction,
                    wind_speed,
                    glide_distance
                )
                
                # Create the map visualization
                m = create_map(search_center)
                
                # Add the last known position marker
                add_last_position_marker(m, latitude, longitude)
                
                # Add the search radius circle
                add_search_radius(m, search_center, search_radius)
                
                # Add the probability heatmap
                add_probability_heatmap(m, probability_points)
                
                # Display the map
                folium_static(m, width=800, height=600)
                
                # Store the calculated data in session state for export
                st.session_state.search_center = search_center
                st.session_state.search_radius = search_radius
                st.session_state.probability_points = probability_points
                
                # Display search area information
                st.subheader("Search Area Information")
                st.write(f"Search center: {search_center[0]:.6f}°N, {search_center[1]:.6f}°E")
                st.write(f"Search radius: {search_radius:.2f} nautical miles")
                st.write(f"Maximum glide distance: {glide_distance:.2f} nautical miles")
                st.write(f"Total search area: {np.pi * search_radius**2:.2f} square nautical miles")

    with col2:
        st.subheader("Aircraft Specifications")
        st.write(f"**Type:** {aircraft_type}")
        st.write(f"**Glide Ratio:** {aircraft_specs['glide_ratio']}")
        st.write(f"**Max Range:** {aircraft_specs['max_range']} nm")
        st.write(f"**Cruise Speed:** {aircraft_specs['cruise_speed']} knots")
        st.write(f"**Max Fuel Endurance:** {aircraft_specs['fuel_endurance']} hours")
        
        st.subheader("Export Options")
        if 'probability_points' in st.session_state:
            export_format = st.selectbox(
                "Export Format",
                options=["CSV", "GeoJSON"],
                help="Choose format to export search coordinates"
            )
            
            if st.button("Export Search Coordinates"):
                export_data = export_search_coordinates(
                    st.session_state.search_center,
                    st.session_state.search_radius,
                    st.session_state.probability_points,
                    export_format
                )
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if export_format == "CSV":
                    filename = f"aircraft_search_{timestamp}.csv"
                    st.download_button(
                        label="Download CSV",
                        data=export_data,
                        file_name=filename,
                        mime="text/csv"
                    )
                else:  # GeoJSON
                    filename = f"aircraft_search_{timestamp}.geojson"
                    st.download_button(
                        label="Download GeoJSON",
                        data=export_data,
                        file_name=filename,
                        mime="application/geo+json"
                    )
        else:
            st.info("Calculate search area first to enable export options")
        
        # Help information
        st.subheader("Quick Guide")
        with st.expander("How to use this tool"):
            st.markdown("""
            1. Enter the last known aircraft position, flight parameters, and environmental conditions in the sidebar
            2. Click "Calculate Search Area" to generate the probability map
            3. The map will show:
               - Last known position (blue marker)
               - Search radius (blue circle)
               - Probability heatmap (red = highest probability)
            4. Export the coordinates for rescue teams using the export options
            """)
        
        with st.expander("Understanding the Results"):
            st.markdown("""
            - **Search Center**: The estimated central point for the search operation
            - **Search Radius**: The maximum distance from the center to search
            - **Probability Heatmap**: Areas with higher probability of finding the aircraft
            - **Factors affecting accuracy**:
              - Quality of last known position data
              - Time since last contact
              - Weather conditions
              - Aircraft condition before loss of contact
            """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center">
        Emergency Use Tool - Always coordinate with aviation authorities and search & rescue teams.
    </div>
    """, unsafe_allow_html=True)
