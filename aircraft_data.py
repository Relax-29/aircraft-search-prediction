# Aircraft specifications database

# Dictionary of aircraft types with their key performance characteristics
# - glide_ratio: How far an aircraft can glide horizontally for each unit of altitude loss
# - max_range: Maximum flying range in nautical miles
# - cruise_speed: Typical cruise speed in knots
# - fuel_endurance: Maximum flying time with full fuel in hours
# - emergency_descent_rate: Typical emergency descent rate in feet per minute
aircraft_types = {
    "Small Single-Engine (Cessna 172)": {
        "glide_ratio": 9.0,
        "max_range": 800,
        "cruise_speed": 122,
        "fuel_endurance": 5.0,
        "emergency_descent_rate": 1500
    },
    "Twin-Engine Piston (Beechcraft Baron)": {
        "glide_ratio": 10.0,
        "max_range": 1500,
        "cruise_speed": 200,
        "fuel_endurance": 6.0,
        "emergency_descent_rate": 1800
    },
    "Small Business Jet (Citation CJ3)": {
        "glide_ratio": 15.0,
        "max_range": 2000,
        "cruise_speed": 415,
        "fuel_endurance": 4.5,
        "emergency_descent_rate": 3000
    },
    "Medium Business Jet (Gulfstream G450)": {
        "glide_ratio": 17.0,
        "max_range": 4350,
        "cruise_speed": 476,
        "fuel_endurance": 9.0,
        "emergency_descent_rate": 3500
    },
    "Regional Airliner (Embraer E175)": {
        "glide_ratio": 18.0,
        "max_range": 2200,
        "cruise_speed": 447,
        "fuel_endurance": 4.5,
        "emergency_descent_rate": 3500
    },
    "Narrow-Body Airliner (Boeing 737)": {
        "glide_ratio": 17.0,
        "max_range": 3400,
        "cruise_speed": 470,
        "fuel_endurance": 6.0,
        "emergency_descent_rate": 4000
    },
    "Wide-Body Airliner (Boeing 777)": {
        "glide_ratio": 19.0,
        "max_range": 7700,
        "cruise_speed": 490,
        "fuel_endurance": 14.0,
        "emergency_descent_rate": 4500
    },
    "Helicopter (Bell 206)": {
        "glide_ratio": 4.0,  # Much lower for helicopters (autorotation)
        "max_range": 430,
        "cruise_speed": 122,
        "fuel_endurance": 3.0,
        "emergency_descent_rate": 1500
    }
}

def get_aircraft_specs(aircraft_type):
    """
    Returns the specifications for a given aircraft type.
    
    Parameters:
    -----------
    aircraft_type : str
        The name of the aircraft type to retrieve specifications for
        
    Returns:
    --------
    dict
        A dictionary containing the specifications for the requested aircraft type
    """
    return aircraft_types.get(aircraft_type, aircraft_types["Small Single-Engine (Cessna 172)"])
