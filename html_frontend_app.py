import streamlit as st
import streamlit.components.v1 as components
import os

def show_html_frontend():
    """
    Display the HTML frontend version of the Aircraft Search & Prediction System
    """
    # Title and description
    st.title("Aircraft Search & Prediction System")
    st.markdown("""
    This advanced version of the aircraft search tool provides real-time tracking capabilities 
    using the OpenSky Network API and includes an emergency landing prediction feature.
    """)
    
    # Create tabs for different sections
    tab1, tab2 = st.tabs(["Interactive Map", "About"])
    
    with tab1:
        # Remove padding/margins for better display
        st.markdown("""
        <style>
            .element-container iframe {
                width: 100%;
                height: 800px;
                border: none;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Instead of loading the HTML file directly, we'll create an iframe pointing to a custom HTML handler
        # to ensure proper loading of all assets and correct API access
        st.markdown("""
        <iframe 
            src="http://localhost:5000/?show=aircraft_tracker" 
            style="width:100%; height:800px; border:none;" 
            allow="geolocation; microphone; camera; midi; vr; accelerometer; gyroscope; payment; ambient-light-sensor; encrypted-media; usb" 
            sandbox="allow-modals allow-forms allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-downloads">
        </iframe>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.header("About the Aircraft Search & Prediction System")
        
        st.subheader("Real-Time Tracking")
        st.markdown("""
        This application connects to the OpenSky Network API to display live aircraft positions on an interactive map.
        Users can search for specific aircraft by call sign, ICAO24 address, or origin country.
        """)
        
        st.subheader("Emergency Landing Prediction")
        st.markdown("""
        The application includes a Glide Prediction Module that calculates potential landing positions
        in the event of engine failure or emergency descent. This is calculated using the glide ratio formula:
        
        **Glide Distance = Altitude × Glide Ratio**
        
        The projected landing coordinates are calculated using trigonometry:
        
        **Landing Position = Current Position + (Distance × cos(θ), Distance × sin(θ))**
        
        where **θ** is the aircraft's track angle converted to radians.
        """)
        
        st.subheader("Technical Details")
        st.markdown("""
        - Frontend: HTML, CSS, JavaScript with Leaflet.js for mapping
        - Styling: Tailwind CSS for responsive design
        - API: OpenSky Network for real-time aircraft data
        - Mathematics: Trigonometric calculations for glide predictions
        
        The system's architecture is modular, with separate components for:
        - Aircraft data handling
        - Map visualization
        - Glide path prediction
        - User interface controls
        """)

if __name__ == "__main__":
    show_html_frontend()