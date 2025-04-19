# Aircraft Search & Prediction System

A comprehensive aircraft tracking and emergency landing prediction system that integrates real-time data visualization, search capabilities, and emergency response tools.

## Features

- Real-time aircraft tracking using OpenSky Network API
- Multiple interface options (Streamlit, HTML/JavaScript)
- Emergency landing prediction with probability heatmaps
- Search capabilities for aircraft by callsign, ICAO24 address, or country
- Database storage for tracking history and predictions
- Interactive maps with multiple visualization options

## Components

- **Streamlit Interface**: Interactive data visualization and user interface
- **RESTful API**: Flask-based backend for database interactions
- **PostgreSQL Database**: Storage for aircraft data, positions, and predictions
- **SQLite Fallback**: Development and testing database when PostgreSQL is unavailable

## Requirements

- Python 3.11+
- PostgreSQL database (optional - falls back to SQLite when unavailable)
- Required Python packages:
  - streamlit
  - flask
  - flask-cors
  - folium
  - streamlit-folium
  - pandas
  - sqlalchemy
  - psycopg2-binary
  - requests
  - numpy

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Relex-29/aircraft-search-prediction.git
   cd aircraft-search-prediction
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   # Start the Streamlit interface
   streamlit run app.py --server.port 5000
   
   # Start the API server (in a separate terminal)
   python aircraft_db_api.py
   ```

## Project Structure

- `app.py`: Main application entry point with Streamlit interface
- `aircraft_db_api.py`: Flask API for database operations
- `database_models.py`: SQLAlchemy models for database tables
- `db_utils.py`: Utility functions for database operations
- `search_algorithm.py`: Core algorithms for search area calculations
- `map_visualization.py`: Map-related visualization utilities

## Usage

The application offers multiple interface options:

1. **Streamlit Interactive**: Classic Streamlit interface with input controls
2. **HTML/JavaScript Version**: Alternative web interface
3. **Aircraft Tracker (Real-time)**: Live aircraft tracking and visualization
4. **Database Records**: View and search stored data

## License

This project is available under the MIT License. See LICENSE file for details.

## Contributors

- Mohit Kumar
- Lakshay Sharma
- Dev Sahu
- Shivi
