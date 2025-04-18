/**
 * Aircraft Data and Specifications
 * Provides aircraft type information and glide ratios
 */

// Aircraft type specifications with glide ratios
const aircraftTypes = {
    'small-single': {
        name: 'Small Single-Engine Aircraft',
        examples: 'Cessna 172, Piper PA-28',
        glideRatio: 9,
        emergencyDescentRate: 1500 // feet per minute
    },
    'twin-engine': {
        name: 'Twin-Engine Piston Aircraft',
        examples: 'Beechcraft Baron, Piper Seneca',
        glideRatio: 10,
        emergencyDescentRate: 1800
    },
    'small-jet': {
        name: 'Small Business Jet',
        examples: 'Citation CJ3, Learjet 45',
        glideRatio: 15,
        emergencyDescentRate: 3000
    },
    'medium-jet': {
        name: 'Medium Business Jet',
        examples: 'Gulfstream G450, Bombardier Challenger',
        glideRatio: 17,
        emergencyDescentRate: 3500
    },
    'regional': {
        name: 'Regional Airliner',
        examples: 'Embraer E175, Bombardier CRJ',
        glideRatio: 18,
        emergencyDescentRate: 3500
    },
    'narrow-body': {
        name: 'Narrow-Body Airliner',
        examples: 'Boeing 737, Airbus A320',
        glideRatio: 17,
        emergencyDescentRate: 4000
    },
    'wide-body': {
        name: 'Wide-Body Airliner',
        examples: 'Boeing 777, Airbus A350',
        glideRatio: 19,
        emergencyDescentRate: 4500
    },
    'helicopter': {
        name: 'Helicopter',
        examples: 'Bell 206, Robinson R44',
        glideRatio: 4, // Much lower for helicopters (autorotation)
        emergencyDescentRate: 1500
    }
};

/**
 * Get aircraft specifications based on type
 * @param {string} aircraftType - The type of aircraft
 * @returns {Object} Aircraft specifications
 */
function getAircraftSpecs(aircraftType) {
    return aircraftTypes[aircraftType] || aircraftTypes['narrow-body']; // Default to narrow-body if type not found
}

/**
 * Convert aircraft transponder code (Mode S code) to aircraft type
 * Note: This is a simplified mapping for demonstration purposes
 * In a real application, this would use a more comprehensive database
 * @param {string} transponderCode - The ICAO24 transponder code
 * @returns {string} Estimated aircraft type category
 */
function estimateAircraftType(transponderCode, callsign) {
    // Some basic pattern matching
    // In a real system, this would use a proper API or database
    
    if (!transponderCode) return 'narrow-body';
    
    // Look at the callsign for some hints
    if (callsign) {
        const callsignUpper = callsign.toUpperCase();
        
        // Check for business jets using common prefixes
        if (callsignUpper.startsWith('N') && callsignUpper.length === 5) {
            return 'small-jet'; // N-numbers with 5 chars often are private aircraft
        }
        
        // Check for regional carriers
        if (callsignUpper.includes('EXP') || callsignUpper.includes('RGN') || 
            callsignUpper.includes('SKW') || callsignUpper.includes('JIA')) {
            return 'regional';
        }
        
        // Check for cargo carriers (often wide-body)
        if (callsignUpper.includes('FDX') || callsignUpper.includes('UPS') || 
            callsignUpper.includes('ABW') || callsignUpper.includes('GTI')) {
            return 'wide-body';
        }
    }
    
    // Use first character of transponder code for a rough estimate
    // This is just for demonstration - not accurate in real world
    const firstChar = transponderCode.charAt(0).toLowerCase();
    
    switch(firstChar) {
        case 'a':
        case 'b':
            return 'wide-body'; // US carriers, many wide-bodies
        case 'c':
            return 'medium-jet'; // Canada, mixed fleet
        case 'd':
            return 'narrow-body'; // Many European carriers
        case 'e':
            return 'regional'; // Many regional/smaller carriers
        case 'f':
            return 'narrow-body'; // Various European
        case '7':
        case '8':
        case '9':
            return 'small-single'; // Often general aviation
        default:
            return 'narrow-body'; // Default to most common type
    }
}

/**
 * Format vertical rate for display
 * @param {number} rate - Vertical rate in feet per minute
 * @returns {string} Formatted string with up/down arrow
 */
function formatVerticalRate(rate) {
    if (!rate || rate === 0) return 'Level';
    
    const absRate = Math.abs(rate);
    const direction = rate > 0 ? '↑' : '↓';
    
    return `${direction} ${absRate.toFixed(0)} ft/min`;
}

/**
 * Format altitude for display
 * @param {number} altitude - Altitude in feet
 * @returns {string} Formatted altitude string
 */
function formatAltitude(altitude) {
    if (!altitude) return 'Unknown';
    return `${Math.round(altitude).toLocaleString()} ft`;
}

/**
 * Format ground speed for display
 * @param {number} speed - Ground speed in knots
 * @returns {string} Formatted speed string
 */
function formatGroundSpeed(speed) {
    if (!speed) return 'Unknown';
    return `${Math.round(speed)} knots`;
}

/**
 * Format heading for display
 * @param {number} heading - Heading in degrees
 * @returns {string} Formatted heading with cardinal direction
 */
function formatHeading(heading) {
    if (heading === undefined || heading === null) return 'Unknown';
    
    // Convert heading to cardinal direction
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                         'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    const index = Math.round(heading / 22.5) % 16;
    
    return `${Math.round(heading)}° (${directions[index]})`;
}