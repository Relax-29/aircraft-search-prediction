// Aircraft specifications database
const aircraftTypes = {
    "cessna172": {
        "name": "Small Single-Engine (Cessna 172)",
        "glide_ratio": 9.0,
        "max_range": 800,
        "cruise_speed": 122,
        "fuel_endurance": 5.0,
        "emergency_descent_rate": 1500
    },
    "baron": {
        "name": "Twin-Engine Piston (Beechcraft Baron)",
        "glide_ratio": 10.0,
        "max_range": 1500,
        "cruise_speed": 200,
        "fuel_endurance": 6.0,
        "emergency_descent_rate": 1800
    },
    "citation": {
        "name": "Small Business Jet (Citation CJ3)",
        "glide_ratio": 15.0,
        "max_range": 2000,
        "cruise_speed": 415,
        "fuel_endurance": 4.5,
        "emergency_descent_rate": 3000
    },
    "gulfstream": {
        "name": "Medium Business Jet (Gulfstream G450)",
        "glide_ratio": 17.0,
        "max_range": 4350,
        "cruise_speed": 476,
        "fuel_endurance": 9.0,
        "emergency_descent_rate": 3500
    },
    "embraer": {
        "name": "Regional Airliner (Embraer E175)",
        "glide_ratio": 18.0,
        "max_range": 2200,
        "cruise_speed": 447,
        "fuel_endurance": 4.5,
        "emergency_descent_rate": 3500
    },
    "boeing737": {
        "name": "Narrow-Body Airliner (Boeing 737)",
        "glide_ratio": 17.0,
        "max_range": 3400,
        "cruise_speed": 470,
        "fuel_endurance": 6.0,
        "emergency_descent_rate": 4000
    },
    "boeing777": {
        "name": "Wide-Body Airliner (Boeing 777)",
        "glide_ratio": 19.0,
        "max_range": 7700,
        "cruise_speed": 490,
        "fuel_endurance": 14.0,
        "emergency_descent_rate": 4500
    },
    "helicopter": {
        "name": "Helicopter (Bell 206)",
        "glide_ratio": 4.0,  // Much lower for helicopters (autorotation)
        "max_range": 430,
        "cruise_speed": 122,
        "fuel_endurance": 3.0,
        "emergency_descent_rate": 1500
    }
};

// Function to update aircraft specs display
function updateAircraftSpecs(aircraftType) {
    const specs = aircraftTypes[aircraftType];
    
    // Update the display
    document.getElementById('spec-type').textContent = specs.name;
    document.getElementById('spec-glide').textContent = specs.glide_ratio.toFixed(1);
    document.getElementById('spec-range').textContent = specs.max_range;
    document.getElementById('spec-speed').textContent = specs.cruise_speed;
    document.getElementById('spec-fuel').textContent = specs.fuel_endurance.toFixed(1);
    
    return specs;
}