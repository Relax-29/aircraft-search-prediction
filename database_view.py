"""
View for displaying database records from the Aircraft Search Prediction System
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import folium
from streamlit_folium import folium_static

# Import database models and functions
from database_models import Aircraft, AircraftPosition, EmergencyPrediction, SearchQuery
from db_utils import (
    get_recent_aircraft, get_aircraft_positions, 
    get_search_history, get_prediction_history,
    find_aircraft_by_callsign, find_aircraft_by_icao24, 
    find_aircraft_by_country, get_aircraft_by_id
)

def show_database_view():
    """
    Display the database records in a Streamlit interface
    """
    st.title("Aircraft Database Records")
    st.markdown("""
    This page displays the records stored in the database for the Aircraft Search Prediction System.
    You can view recent aircraft, their positions, search history, and emergency predictions.
    """)
    
    # Create tabs for different record types
    tab1, tab2, tab3, tab4 = st.tabs(["Aircraft", "Positions", "Searches", "Predictions"])
    
    with tab1:
        show_aircraft_records()
    
    with tab2:
        show_position_records()
    
    with tab3:
        show_search_records()
    
    with tab4:
        show_prediction_records()

def show_aircraft_records():
    """Display aircraft records"""
    st.header("Aircraft Records")
    
    # Search options
    search_col1, search_col2 = st.columns([1, 3])
    
    with search_col1:
        search_type = st.selectbox(
            "Search By",
            ["Recent", "Callsign", "ICAO24", "Country"]
        )
    
    with search_col2:
        if search_type == "Recent":
            limit = st.slider("Number of Records", 5, 100, 20)
            search_value = None
        else:
            search_value = st.text_input(f"Enter {search_type}")
    
    if st.button("Search Aircraft"):
        with st.spinner("Searching..."):
            if search_type == "Recent":
                aircraft_list = get_recent_aircraft(limit=limit)
            elif search_type == "Callsign":
                aircraft_list = find_aircraft_by_callsign(search_value)
            elif search_type == "ICAO24":
                aircraft_list = find_aircraft_by_icao24(search_value)
            elif search_type == "Country":
                aircraft_list = find_aircraft_by_country(search_value)
            
            # Display results
            if aircraft_list:
                # Convert to DataFrame for display
                data = []
                for a in aircraft_list:
                    data.append({
                        "ID": a.id,
                        "ICAO24": a.icao24,
                        "Callsign": a.callsign or "N/A",
                        "Aircraft Type": a.aircraft_type or "Unknown",
                        "Origin Country": a.origin_country or "Unknown",
                        "Last Updated": a.last_updated.strftime("%Y-%m-%d %H:%M:%S") if a.last_updated else "N/A"
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
                
                # Store in session state for selection
                st.session_state.aircraft_list = aircraft_list
                
                # Let user select an aircraft to view details
                aircraft_ids = [a.id for a in aircraft_list]
                if aircraft_ids:
                    selected_id = st.selectbox(
                        "Select Aircraft to View Positions",
                        options=aircraft_ids,
                        format_func=lambda x: f"ID: {x} - {next((a.callsign for a in aircraft_list if a.id == x), 'Unknown')}"
                    )
                    
                    if st.button("View Positions"):
                        st.session_state.selected_aircraft_id = selected_id
                        st.session_state.show_positions = True
            else:
                st.info("No aircraft found matching the search criteria.")
    
    # Show positions if selected
    if 'show_positions' in st.session_state and st.session_state.show_positions:
        if 'selected_aircraft_id' in st.session_state:
            show_aircraft_positions(st.session_state.selected_aircraft_id)

def show_aircraft_positions(aircraft_id):
    """Display positions for a specific aircraft"""
    aircraft = get_aircraft_by_id(aircraft_id)
    
    if not aircraft:
        st.error(f"Aircraft with ID {aircraft_id} not found.")
        return
    
    st.subheader(f"Positions for {aircraft.callsign or aircraft.icao24}")
    
    # Get positions
    positions = get_aircraft_positions(aircraft_id, limit=50)
    
    if not positions:
        st.info("No position records found for this aircraft.")
        return
    
    # Display positions in a table
    data = []
    for p in positions:
        data.append({
            "Timestamp": p.timestamp.strftime("%Y-%m-%d %H:%M:%S") if p.timestamp else "N/A",
            "Latitude": p.latitude,
            "Longitude": p.longitude,
            "Altitude (ft)": int(p.altitude) if p.altitude else "N/A",
            "Ground Speed (kts)": int(p.ground_speed) if p.ground_speed else "N/A",
            "Heading (°)": int(p.heading) if p.heading else "N/A",
            "Vertical Speed (ft/min)": int(p.vertical_speed) if p.vertical_speed else "N/A",
            "On Ground": "Yes" if p.on_ground else "No"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df)
    
    # Show map of positions
    st.subheader("Position Map")
    
    # Create map centered on the most recent position
    latest_pos = positions[0]
    m = folium.Map(
        location=[latest_pos.latitude, latest_pos.longitude],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add markers for each position
    coordinates = []
    for p in reversed(positions):  # Reverse to show oldest to newest
        coordinates.append([p.latitude, p.longitude])
        
        # Create popup text
        popup_text = f"""
        <b>Time:</b> {p.timestamp.strftime('%Y-%m-%d %H:%M:%S') if p.timestamp else 'N/A'}<br>
        <b>Altitude:</b> {int(p.altitude) if p.altitude else 'N/A'} ft<br>
        <b>Speed:</b> {int(p.ground_speed) if p.ground_speed else 'N/A'} kts<br>
        <b>Heading:</b> {int(p.heading) if p.heading else 'N/A'}°<br>
        <b>Vertical Rate:</b> {int(p.vertical_speed) if p.vertical_speed else 'N/A'} ft/min
        """
        
        # Add marker
        folium.Marker(
            location=[p.latitude, p.longitude],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color='blue' if p != latest_pos else 'red', icon='plane', prefix='fa')
        ).add_to(m)
    
    # Add polyline connecting the points
    if len(coordinates) > 1:
        folium.PolyLine(
            coordinates,
            color='blue',
            weight=3,
            opacity=0.7,
            dash_array='5'
        ).add_to(m)
    
    # Display the map
    folium_static(m, width=800, height=500)

def show_position_records():
    """Display position records"""
    st.header("Position Records")
    
    # Let user select an aircraft to view positions
    st.subheader("Select Aircraft")
    
    search_col1, search_col2 = st.columns([1, 3])
    
    with search_col1:
        search_type = st.selectbox(
            "Search Aircraft By",
            ["Callsign", "ICAO24", "Country", "ID"],
            key="pos_search_type"
        )
    
    with search_col2:
        if search_type == "ID":
            search_value = st.number_input("Enter Aircraft ID", min_value=1, step=1)
        else:
            search_value = st.text_input(f"Enter {search_type}", key="pos_search_value")
    
    if st.button("Find Aircraft"):
        with st.spinner("Searching..."):
            if search_type == "Callsign":
                aircraft_list = find_aircraft_by_callsign(search_value)
            elif search_type == "ICAO24":
                aircraft_list = find_aircraft_by_icao24(search_value)
            elif search_type == "Country":
                aircraft_list = find_aircraft_by_country(search_value)
            elif search_type == "ID":
                aircraft = get_aircraft_by_id(search_value)
                aircraft_list = [aircraft] if aircraft else []
            
            # Display results
            if aircraft_list:
                # Convert to DataFrame for display
                data = []
                for a in aircraft_list:
                    data.append({
                        "ID": a.id,
                        "ICAO24": a.icao24,
                        "Callsign": a.callsign or "N/A",
                        "Aircraft Type": a.aircraft_type or "Unknown",
                        "Origin Country": a.origin_country or "Unknown",
                        "Last Updated": a.last_updated.strftime("%Y-%m-%d %H:%M:%S") if a.last_updated else "N/A"
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df)
                
                # Let user select an aircraft to view positions
                aircraft_ids = [a.id for a in aircraft_list]
                if aircraft_ids:
                    selected_id = st.selectbox(
                        "Select Aircraft",
                        options=aircraft_ids,
                        format_func=lambda x: f"ID: {x} - {next((a.callsign for a in aircraft_list if a.id == x), 'Unknown')}",
                        key="pos_aircraft_select"
                    )
                    
                    if st.button("View Positions", key="view_pos_btn"):
                        show_aircraft_positions(selected_id)
            else:
                st.info("No aircraft found matching the search criteria.")

def show_search_records():
    """Display search history records"""
    st.header("Search History")
    
    # Get search history
    time_period = st.selectbox(
        "Time Period",
        ["Last 24 Hours", "Last Week", "Last Month", "All Time"]
    )
    
    if st.button("View Search History"):
        # Get appropriate limit based on time period
        if time_period == "Last 24 Hours":
            limit = 500
        elif time_period == "Last Week":
            limit = 1000
        elif time_period == "Last Month":
            limit = 5000
        else:  # All Time
            limit = 10000
        
        searches = get_search_history(limit=limit)
        
        # Filter by time period if needed
        if time_period != "All Time":
            now = datetime.utcnow()
            if time_period == "Last 24 Hours":
                cutoff = now - timedelta(days=1)
            elif time_period == "Last Week":
                cutoff = now - timedelta(days=7)
            elif time_period == "Last Month":
                cutoff = now - timedelta(days=30)
                
            searches = [s for s in searches if s.timestamp and s.timestamp >= cutoff]
        
        if searches:
            # Display in a table
            data = []
            for s in searches:
                data.append({
                    "ID": s.id,
                    "Search Type": s.search_type,
                    "Search Value": s.search_value,
                    "Timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S") if s.timestamp else "N/A"
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            # Basic analytics
            st.subheader("Search Analytics")
            
            # Searches per day
            if searches and searches[0].timestamp:
                st.write("### Searches Per Day")
                
                # Group by day
                dates = [s.timestamp.date() for s in searches if s.timestamp]
                date_counts = {}
                for date in dates:
                    date_counts[date] = date_counts.get(date, 0) + 1
                
                # Create DataFrame for chart
                date_df = pd.DataFrame({
                    "Date": list(date_counts.keys()),
                    "Count": list(date_counts.values())
                })
                
                date_df = date_df.sort_values("Date")
                st.bar_chart(date_df.set_index("Date"))
            
            # Search types distribution
            st.write("### Search Types Distribution")
            type_counts = {}
            for s in searches:
                type_counts[s.search_type] = type_counts.get(s.search_type, 0) + 1
            
            type_df = pd.DataFrame({
                "Search Type": list(type_counts.keys()),
                "Count": list(type_counts.values())
            })
            
            # Use columns for chart and data
            type_col1, type_col2 = st.columns([2, 1])
            
            with type_col1:
                st.bar_chart(type_df.set_index("Search Type"))
            
            with type_col2:
                st.dataframe(type_df)
        else:
            st.info("No search history found for the selected time period.")

def show_prediction_records():
    """Display emergency prediction records"""
    st.header("Emergency Landing Predictions")
    
    # Get prediction history
    time_period = st.selectbox(
        "Time Period",
        ["Last 24 Hours", "Last Week", "Last Month", "All Time"],
        key="pred_time_period"
    )
    
    if st.button("View Prediction History"):
        # Get appropriate limit based on time period
        if time_period == "Last 24 Hours":
            limit = 500
        elif time_period == "Last Week":
            limit = 1000
        elif time_period == "Last Month":
            limit = 5000
        else:  # All Time
            limit = 10000
        
        predictions = get_prediction_history(limit=limit)
        
        # Filter by time period if needed
        if time_period != "All Time":
            now = datetime.utcnow()
            if time_period == "Last 24 Hours":
                cutoff = now - timedelta(days=1)
            elif time_period == "Last Week":
                cutoff = now - timedelta(days=7)
            elif time_period == "Last Month":
                cutoff = now - timedelta(days=30)
                
            predictions = [p for p in predictions if p.timestamp and p.timestamp >= cutoff]
        
        if predictions:
            # Display in a table
            data = []
            for p in predictions:
                aircraft = get_aircraft_by_id(p.aircraft_id)
                aircraft_info = f"{aircraft.callsign or aircraft.icao24}" if aircraft else f"ID: {p.aircraft_id}"
                
                data.append({
                    "ID": p.id,
                    "Aircraft": aircraft_info,
                    "Timestamp": p.timestamp.strftime("%Y-%m-%d %H:%M:%S") if p.timestamp else "N/A",
                    "Aircraft Type": p.aircraft_type or "Unknown",
                    "Glide Distance (nm)": round(p.glide_distance, 2) if p.glide_distance else "N/A",
                    "Glide Time (min)": round(p.glide_time, 2) if p.glide_time else "N/A"
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            # Let user select a prediction to view on map
            if predictions:
                selected_id = st.selectbox(
                    "Select Prediction to View on Map",
                    options=[p.id for p in predictions],
                    format_func=lambda x: f"ID: {x} - {next((p.timestamp.strftime('%Y-%m-%d %H:%M:%S') if p.timestamp else 'N/A' for p in predictions if p.id == x), 'Unknown')}"
                )
                
                if st.button("View Prediction Map"):
                    show_prediction_map(selected_id, predictions)
        else:
            st.info("No prediction history found for the selected time period.")

def show_prediction_map(prediction_id, predictions):
    """Show prediction on a map"""
    # Find the prediction
    prediction = next((p for p in predictions if p.id == prediction_id), None)
    
    if not prediction:
        st.error(f"Prediction with ID {prediction_id} not found.")
        return
    
    st.subheader(f"Emergency Landing Prediction {prediction_id}")
    
    # Get aircraft details
    aircraft = get_aircraft_by_id(prediction.aircraft_id)
    aircraft_info = f"{aircraft.callsign or aircraft.icao24}" if aircraft else f"ID: {prediction.aircraft_id}"
    
    # Display prediction details
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Aircraft:** {aircraft_info}")
        st.write(f"**Time:** {prediction.timestamp.strftime('%Y-%m-%d %H:%M:%S') if prediction.timestamp else 'N/A'}")
        st.write(f"**Aircraft Type:** {prediction.aircraft_type or 'Unknown'}")
        st.write(f"**Glide Ratio:** {prediction.glide_ratio}")
    
    with col2:
        st.write(f"**Altitude:** {int(prediction.altitude) if prediction.altitude else 'N/A'} ft")
        st.write(f"**Glide Distance:** {round(prediction.glide_distance, 2) if prediction.glide_distance else 'N/A'} nm")
        st.write(f"**Glide Time:** {round(prediction.glide_time, 2) if prediction.glide_time else 'N/A'} min")
        st.write(f"**Uncertainty Radius:** {round(prediction.uncertainty_radius, 2) if prediction.uncertainty_radius else 'N/A'} km")
    
    # Create map
    m = folium.Map(
        location=[prediction.latitude, prediction.longitude],
        zoom_start=9,
        tiles='OpenStreetMap'
    )
    
    # Add aircraft position marker
    folium.Marker(
        location=[prediction.latitude, prediction.longitude],
        popup=f"Aircraft Position<br>Altitude: {int(prediction.altitude) if prediction.altitude else 'N/A'} ft",
        icon=folium.Icon(color='blue', icon='plane', prefix='fa')
    ).add_to(m)
    
    # Add landing position marker
    folium.Marker(
        location=[prediction.predicted_landing_latitude, prediction.predicted_landing_longitude],
        popup="Predicted Landing Position",
        icon=folium.Icon(color='red', icon='circle', prefix='fa')
    ).add_to(m)
    
    # Add glide path line
    folium.PolyLine(
        locations=[
            [prediction.latitude, prediction.longitude],
            [prediction.predicted_landing_latitude, prediction.predicted_landing_longitude]
        ],
        color='orange',
        weight=3,
        opacity=0.8,
        dash_array='5'
    ).add_to(m)
    
    # Add uncertainty circle
    if prediction.uncertainty_radius:
        folium.Circle(
            location=[prediction.predicted_landing_latitude, prediction.predicted_landing_longitude],
            radius=prediction.uncertainty_radius * 1000,  # Convert km to meters
            color='red',
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
    
    # Display the map
    folium_static(m, width=800, height=500)

if __name__ == "__main__":
    show_database_view()