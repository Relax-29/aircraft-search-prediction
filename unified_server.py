import streamlit as st
from streamlit.web.server.server import Server
import threading
import http.server
import socketserver
import os
import time
from streamlit.runtime.scriptrunner import get_script_run_ctx
import webbrowser

# Determine if we're in Streamlit mode or HTML mode
import sys

# Path to the frontend files
STATIC_DIR = "static"

def serve_html_frontend():
    # Create a simple server to serve static HTML/JS/CSS files
    os.chdir(STATIC_DIR)
    
    # Create the handler
    class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            return super(CORSHTTPRequestHandler, self).end_headers()
    
    # Use a high port for the internal server
    PORT = 8099
    Handler = CORSHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"HTML frontend server started at http://localhost:{PORT}")
        httpd.serve_forever()

def main():
    # Set page config for streamlit
    st.set_page_config(
        page_title="Aircraft Search Location Calculator",
        page_icon="✈️",
        layout="wide"
    )
    
    # Add a button to switch to HTML mode
    st.sidebar.title("Frontend Options")
    if st.sidebar.button("Switch to HTML/JS Frontend"):
        st.markdown(
            f"""
            <iframe src="/static/index.html" width="100%" height="800px"></iframe>
            """,
            unsafe_allow_html=True
        )
    else:
        # Import and run the original Streamlit app
        import app
    
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--html":
        # Start in HTML mode
        serve_html_frontend()
    else:
        # Start Streamlit mode
        main()