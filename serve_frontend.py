"""
Utility to serve the Aircraft Tracker frontend
"""
import streamlit as st
import streamlit.components.v1 as components
import os

def serve_tracker_frontend():
    """
    Serve the Aircraft Tracker frontend as a standalone page
    This function is used when the frontend is loaded in an iframe
    """
    # Check query parameters for the 'show' parameter
    query_params = st.query_params
    if 'show' in query_params and query_params['show'] == 'aircraft_tracker':
        # No Streamlit UI elements
        hide_streamlit_ui()
        
        # Load and render the tracker HTML directly
        serve_html_file('aircraft-tracker/index.html')
        
        # Prevent the default Streamlit app from running
        st.stop()
        
def hide_streamlit_ui():
    """Hide all Streamlit UI elements"""
    st.markdown("""
    <style>
        #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0px;}
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .main .block-container {
            padding-top: 0;
            padding-bottom: 0;
            padding-left: 0;
            padding-right: 0;
            max-width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)

def serve_html_file(file_path):
    """Load and serve an HTML file directly"""
    if not os.path.exists(file_path):
        st.error(f"Could not find HTML file at {file_path}")
        return
        
    try:
        with open(file_path, 'r') as f:
            html_content = f.read()
            
        # Replace relative paths for resources
        html_content = html_content.replace('src="js/', f'src="aircraft-tracker/js/')
        html_content = html_content.replace('href="css/', f'href="aircraft-tracker/css/')
            
        # Display the HTML content
        components.html(html_content, height=1000, width=1000, scrolling=False)
    except Exception as e:
        st.error(f"Error loading HTML file: {str(e)}")