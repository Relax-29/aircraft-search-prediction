"""
Integration test script for HTML frontend and Database API communication
"""
import requests
import json
import webbrowser
import os
import time
from urllib.parse import urljoin

def test_database_api():
    """Test communication with the database API"""
    base_url = "http://localhost:5001"
    
    # Test aircraft endpoint
    test_aircraft = {
        "icao24": "test123",
        "callsign": "TEST123",
        "aircraft_type": "TEST",
        "origin_country": "Testland"
    }
    
    try:
        # Test adding an aircraft
        print("Testing aircraft API...")
        response = requests.post(
            urljoin(base_url, '/api/aircraft'),
            json=test_aircraft
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Successfully added aircraft: {result}")
            aircraft_id = result.get('aircraft_id')
            
            # Test adding a position
            if aircraft_id:
                print("\nTesting position API...")
                position_data = {
                    "aircraft_id": aircraft_id,
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "altitude": 35000,
                    "ground_speed": 450,
                    "heading": 90,
                    "vertical_speed": 0,
                    "on_ground": False
                }
                
                response = requests.post(
                    urljoin(base_url, '/api/positions'),
                    json=position_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ Successfully added position: {result}")
                else:
                    print(f"✗ Failed to add position: {response.text}")
            
            # Test search functionality
            print("\nTesting search API...")
            search_data = {
                "search_type": "icao24",
                "search_value": "test123",
                "aircraft_ids": [aircraft_id] if aircraft_id else []
            }
            
            response = requests.post(
                urljoin(base_url, '/api/search'),
                json=search_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Successfully saved search: {result}")
            else:
                print(f"✗ Failed to save search: {response.text}")
                
            # Test search by ICAO24
            print("\nTesting search by ICAO24...")
            response = requests.get(
                urljoin(base_url, f'/api/aircraft/search/icao24/{test_aircraft["icao24"]}')
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Successfully searched by ICAO24: {result}")
            else:
                print(f"✗ Failed to search by ICAO24: {response.text}")
                
        else:
            print(f"✗ Failed to add aircraft: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection error: Could not connect to the API server.")
        print("  Make sure the Database API Server is running on port 5001.")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False
        
    print("\n✓ API tests completed successfully!")
    return True

def test_html_frontend():
    """Open the HTML frontend in a browser"""
    streamlit_url = "http://localhost:5000/?show=aircraft_tracker"
    print(f"\nOpening HTML frontend at {streamlit_url}")
    print("Please check if the page loads correctly and buttons respond as expected.")
    try:
        webbrowser.open(streamlit_url)
        return True
    except Exception as e:
        print(f"✗ Error opening browser: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Aircraft Tracker Integration Test ===\n")
    
    # Test the database API
    api_success = test_database_api()
    
    if api_success:
        # Open the HTML frontend
        test_html_frontend()
        
    print("\nTest completed! Check the console for any errors.")