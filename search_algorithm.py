import numpy as np
from utils import haversine_distance, get_destination_point

def calculate_search_area(latitude, longitude, altitude, ground_speed, heading, 
                         vertical_speed, wind_speed, wind_direction, aircraft_specs, search_radius_multiplier):
    """
    Calculate the search area based on the last known aircraft position and flight parameters.
    
    Parameters:
    -----------
    latitude : float
        Last known latitude in decimal degrees
    longitude : float
        Last known longitude in decimal degrees
    altitude : float
        Last known altitude in feet
    ground_speed : float
        Last known ground speed in knots
    heading : float
        Last known heading in degrees
    vertical_speed : float
        Last known vertical speed in feet per minute
    wind_speed : float
        Wind speed in knots
    wind_direction : float
        Wind direction in degrees
    aircraft_specs : dict
        Dictionary containing aircraft specifications
    search_radius_multiplier : float
        Multiplier to increase the search radius beyond the calculated minimum
        
    Returns:
    --------
    tuple
        (search_center, search_radius, glide_distance)
        search_center: (lat, lon) of the estimated crash site center
        search_radius: radius of search area in nautical miles
        glide_distance: maximum glide distance in nautical miles
    """
    # Convert altitude from feet to nautical miles (1 nm = 6076 feet)
    altitude_nm = altitude / 6076
    
    # Calculate maximum glide distance based on glide ratio and altitude
    glide_distance = altitude_nm * aircraft_specs["glide_ratio"]
    
    # Calculate time to impact based on vertical speed (minutes)
    # If vertical speed is zero or positive, use a conservative estimate based on emergency descent rate
    if vertical_speed <= 0:
        time_to_impact_minutes = altitude / abs(vertical_speed) if vertical_speed < 0 else altitude / aircraft_specs["emergency_descent_rate"]
    else:
        # If climbing, assume emergency and use emergency descent rate
        time_to_impact_minutes = altitude / aircraft_specs["emergency_descent_rate"]
    
    # Convert time to hours
    time_to_impact_hours = time_to_impact_minutes / 60
    
    # Calculate horizontal distance traveled during descent (nautical miles)
    horizontal_distance = ground_speed * time_to_impact_hours
    
    # Calculate the initial search center based on heading and horizontal distance
    initial_center_lat, initial_center_lon = get_destination_point(
        latitude, longitude, heading, horizontal_distance)
    
    # Adjust for wind effect
    # Calculate wind effect distance (wind speed * time to impact)
    wind_distance = wind_speed * time_to_impact_hours
    
    # Calculate the final search center with wind adjustment
    final_center_lat, final_center_lon = get_destination_point(
        initial_center_lat, initial_center_lon, wind_direction, wind_distance)
    
    # Calculate search radius:
    # Base radius on the larger of glide distance or horizontal distance traveled
    base_radius = max(glide_distance, horizontal_distance)
    
    # Add uncertainty based on wind
    wind_uncertainty = wind_distance * 0.2  # 20% of wind distance
    
    # Apply search radius multiplier for safety margin
    search_radius = (base_radius + wind_uncertainty) * search_radius_multiplier
    
    return (final_center_lat, final_center_lon), search_radius, glide_distance

def calculate_probability_distribution(search_center, search_radius, num_points, heading, 
                                      wind_direction, wind_speed, glide_distance):
    """
    Generate a probability distribution of potential crash sites within the search area.
    
    Parameters:
    -----------
    search_center : tuple
        (latitude, longitude) of the search center
    search_radius : float
        Radius of the search area in nautical miles
    num_points : int
        Number of points to generate for the probability distribution
    heading : float
        Last known heading in degrees
    wind_direction : float
        Wind direction in degrees
    wind_speed : float
        Wind speed in knots
    glide_distance : float
        Maximum glide distance in nautical miles
        
    Returns:
    --------
    list
        List of [lat, lon, probability] points representing the probability distribution
    """
    # Convert degrees to radians for calculations
    heading_rad = np.radians(heading)
    wind_direction_rad = np.radians(wind_direction)
    
    # Generate random points within the search radius
    # Use a gaussian distribution with higher concentration in the direction of travel and wind
    center_lat, center_lon = search_center
    
    # Calculate the direction of highest probability (combination of heading and wind direction)
    # Weight heading and wind direction based on wind speed (higher wind = higher weight)
    wind_weight = min(wind_speed / 50, 0.8)  # cap at 80%
    heading_weight = 1 - wind_weight
    
    # Convert heading and wind direction to x,y components
    heading_x = np.cos(heading_rad)
    heading_y = np.sin(heading_rad)
    wind_x = np.cos(wind_direction_rad)
    wind_y = np.sin(wind_direction_rad)
    
    # Calculate the weighted direction
    direction_x = heading_weight * heading_x + wind_weight * wind_x
    direction_y = heading_weight * heading_y + wind_weight * wind_y
    
    # Convert back to angle
    high_prob_direction = np.arctan2(direction_y, direction_x)
    
    # Generate random distances from center (with bias toward the max probable direction)
    distances = np.random.rayleigh(scale=search_radius/2, size=num_points)
    distances = np.clip(distances, 0, search_radius)
    
    # Generate random angles with bias toward the high probability direction
    kappa = 2.0  # Concentration parameter (higher = more concentrated)
    angles = np.random.vonmises(mu=high_prob_direction, kappa=kappa, size=num_points)
    
    # Convert polar coordinates to Cartesian
    x = distances * np.cos(angles)
    y = distances * np.sin(angles)
    
    # Calculate probabilities based on distance from center and alignment with high probability direction
    # Points closer to the center and aligned with the high probability direction have higher probability
    max_distance = search_radius
    distance_from_center = np.sqrt(x**2 + y**2)
    
    # Calculate the angle difference between point and high probability direction
    angle_diff = np.abs(np.arctan2(y, x) - high_prob_direction)
    angle_diff = np.minimum(angle_diff, 2*np.pi - angle_diff)  # Ensure the difference is the smaller angle
    
    # Calculate probability based on distance and angle
    # Exponential decay with distance from center
    distance_factor = np.exp(-1.5 * distance_from_center / max_distance)
    # Cosine factor for angle (1 when aligned with high prob direction, decreasing as angle increases)
    angle_factor = np.cos(angle_diff)**2
    
    # Combine factors into final probability
    probability = distance_factor * (0.7 + 0.3 * angle_factor)
    
    # Normalize probabilities
    probability = probability / np.max(probability)
    
    # Convert x,y offsets to lat/lon points
    earth_radius_nm = 3440.065  # Earth radius in nautical miles
    lat_points = center_lat + np.degrees(y / earth_radius_nm)
    lon_points = center_lon + np.degrees(x / (earth_radius_nm * np.cos(np.radians(center_lat))))
    
    # Combine into result list
    results = []
    for i in range(num_points):
        results.append([lat_points[i], lon_points[i], float(probability[i])])
    
    return results
