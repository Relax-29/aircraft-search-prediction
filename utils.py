import numpy as np
import math
import json
import io
import csv

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    
    Parameters:
    -----------
    lat1, lon1 : float
        Latitude and longitude of point 1 in decimal degrees
    lat2, lon2 : float
        Latitude and longitude of point 2 in decimal degrees
        
    Returns:
    --------
    float
        Distance between the points in nautical miles
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in nautical miles
    r = 3440.065
    
    return c * r

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate the bearing between two points.
    
    Parameters:
    -----------
    lat1, lon1 : float
        Latitude and longitude of point 1 in decimal degrees
    lat2, lon2 : float
        Latitude and longitude of point 2 in decimal degrees
        
    Returns:
    --------
    float
        Bearing angle in degrees
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Calculate bearing
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    
    bearing = math.atan2(y, x)
    
    # Convert to degrees
    bearing = math.degrees(bearing)
    
    # Normalize to 0-360
    bearing = (bearing + 360) % 360
    
    return bearing

def get_destination_point(lat, lon, bearing, distance):
    """
    Calculate the destination point given a starting point, bearing, and distance.
    
    Parameters:
    -----------
    lat, lon : float
        Latitude and longitude of starting point in decimal degrees
    bearing : float
        Bearing angle in degrees
    distance : float
        Distance to travel in nautical miles
        
    Returns:
    --------
    tuple
        (lat, lon) of the destination point in decimal degrees
    """
    # Convert decimal degrees to radians
    lat = math.radians(lat)
    lon = math.radians(lon)
    bearing = math.radians(bearing)
    
    # Earth radius in nautical miles
    earth_radius = 3440.065
    
    # Calculate destination point
    lat2 = math.asin(math.sin(lat) * math.cos(distance/earth_radius) + 
                     math.cos(lat) * math.sin(distance/earth_radius) * math.cos(bearing))
    
    lon2 = lon + math.atan2(math.sin(bearing) * math.sin(distance/earth_radius) * math.cos(lat),
                           math.cos(distance/earth_radius) - math.sin(lat) * math.sin(lat2))
    
    # Convert back to degrees
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)
    
    return lat2, lon2

def export_search_coordinates(search_center, search_radius, probability_points, export_format):
    """
    Export search area coordinates in the specified format.
    
    Parameters:
    -----------
    search_center : tuple
        (latitude, longitude) of the search center
    search_radius : float
        Radius of the search area in nautical miles
    probability_points : list
        List of [lat, lon, probability] points representing the probability distribution
    export_format : str
        Format to export the data in ('CSV' or 'GeoJSON')
        
    Returns:
    --------
    str
        String containing the exported data in the specified format
    """
    if export_format == "CSV":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Latitude", "Longitude", "Probability", "Type"])
        
        # Write search center
        writer.writerow([search_center[0], search_center[1], 1.0, "center"])
        
        # Write search area boundary points
        num_boundary_points = 36  # One point every 10 degrees
        for i in range(num_boundary_points):
            angle = math.radians(i * 10)
            lat, lon = get_destination_point(search_center[0], search_center[1], 
                                           math.degrees(angle), search_radius)
            writer.writerow([lat, lon, 0.0, "boundary"])
        
        # Write probability points (only include points with probability > 0.2 to keep file size reasonable)
        significant_points = [p for p in probability_points if p[2] > 0.2]
        for point in significant_points:
            writer.writerow([point[0], point[1], point[2], "probability"])
        
        return output.getvalue()
    
    else:  # GeoJSON
        features = []
        
        # Add search center
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [search_center[1], search_center[0]]  # GeoJSON uses [lon, lat]
            },
            "properties": {
                "type": "center",
                "probability": 1.0,
                "description": "Search Area Center"
            }
        })
        
        # Add search area boundary
        boundary_coords = []
        num_boundary_points = 36  # One point every 10 degrees
        for i in range(num_boundary_points + 1):  # +1 to close the loop
            angle = math.radians(i % 36 * 10)
            lat, lon = get_destination_point(search_center[0], search_center[1], 
                                           math.degrees(angle), search_radius)
            boundary_coords.append([lon, lat])  # GeoJSON uses [lon, lat]
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [boundary_coords]
            },
            "properties": {
                "type": "boundary",
                "description": f"Search Area Boundary ({search_radius:.2f} nm radius)"
            }
        })
        
        # Add high probability points (only include points with probability > 0.5)
        high_prob_points = [p for p in probability_points if p[2] > 0.5]
        for point in high_prob_points:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point[1], point[0]]  # GeoJSON uses [lon, lat]
                },
                "properties": {
                    "type": "probability",
                    "probability": point[2],
                    "description": f"Probability: {point[2]:.2f}"
                }
            })
        
        # Create GeoJSON object
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return json.dumps(geojson, indent=2)
