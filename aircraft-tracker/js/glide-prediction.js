/**
 * Glide Prediction Module
 * Calculates potential landing locations in case of emergency
 */

// Constants for calculations
const EARTH_RADIUS_METERS = 6371000; // Earth radius in meters
const FEET_TO_METERS = 0.3048; // Conversion factor from feet to meters
const NAUTICAL_MILE_TO_METERS = 1852; // Conversion factor from nautical miles to meters
const KNOTS_TO_MS = 0.51444; // Conversion factor from knots to m/s

/**
 * Calculate glide distance based on altitude and glide ratio
 * @param {number} altitude - Aircraft altitude in feet
 * @param {number} glideRatio - Aircraft glide ratio (distance:height)
 * @returns {number} Maximum glide distance in meters
 */
function calculateGlideDistance(altitude, glideRatio) {
    // Convert altitude to meters and apply glide ratio
    const altitudeMeters = altitude * FEET_TO_METERS;
    return altitudeMeters * glideRatio;
}

/**
 * Calculate destination point given starting position, bearing and distance
 * @param {Array} startPoint - Starting position [latitude, longitude] in degrees
 * @param {number} bearing - Bearing in degrees
 * @param {number} distance - Distance in meters
 * @returns {Array} Destination point [latitude, longitude] in degrees
 */
function calculateDestinationPoint(startPoint, bearing, distance) {
    // Convert to radians
    const lat1 = toRadians(startPoint[0]);
    const lon1 = toRadians(startPoint[1]);
    const bearingRad = toRadians(bearing);
    
    // Calculate angular distance
    const angularDistance = distance / EARTH_RADIUS_METERS;
    
    // Calculate destination point
    const lat2 = Math.asin(
        Math.sin(lat1) * Math.cos(angularDistance) +
        Math.cos(lat1) * Math.sin(angularDistance) * Math.cos(bearingRad)
    );
    
    const lon2 = lon1 + Math.atan2(
        Math.sin(bearingRad) * Math.sin(angularDistance) * Math.cos(lat1),
        Math.cos(angularDistance) - Math.sin(lat1) * Math.sin(lat2)
    );
    
    // Convert back to degrees and normalize longitude
    return [toDegrees(lat2), ((toDegrees(lon2) + 540) % 360) - 180];
}

/**
 * Calculate landing zone considering wind effects
 * @param {Object} aircraft - Aircraft data with position, altitude, heading, etc.
 * @param {Object} aircraftSpecs - Aircraft specifications including glide ratio
 * @param {Object} windConditions - Wind speed and direction
 * @returns {Object} Landing zone prediction data
 */
function predictLandingZone(aircraft, aircraftSpecs, windConditions) {
    // Extract required values
    const position = [aircraft.latitude, aircraft.longitude];
    const altitude = aircraft.geo_altitude || aircraft.baro_altitude || 0;
    const heading = aircraft.true_track || 0;
    const groundSpeed = aircraft.velocity || 0;
    
    // Extract wind data
    const windSpeed = windConditions.speed || 0;
    const windDirection = windConditions.direction || 0;
    
    // Calculate basic glide distance
    const glideRatio = aircraftSpecs.glideRatio || 10;
    const glideDistanceMeters = calculateGlideDistance(altitude, glideRatio);
    const glideDistanceNM = glideDistanceMeters / NAUTICAL_MILE_TO_METERS;
    
    // Time to glide (in seconds)
    const timeToGlide = altitude / (aircraftSpecs.emergencyDescentRate || 1500) * 60;
    
    // Calculate wind effect
    const windSpeedMS = windSpeed * KNOTS_TO_MS;
    const windEffectDistance = windSpeedMS * timeToGlide;
    
    // Calculate initial landing point based on heading
    const initialLandingPoint = calculateDestinationPoint(position, heading, glideDistanceMeters);
    
    // Adjust for wind effect
    const finalLandingPoint = calculateDestinationPoint(initialLandingPoint, windDirection, windEffectDistance);
    
    // Calculate uncertainty radius (10% of glide distance + wind uncertainty)
    const windUncertainty = windEffectDistance * 0.2;
    const uncertaintyRadiusMeters = glideDistanceMeters * 0.1 + windUncertainty;
    
    return {
        aircraftPosition: position,
        landingPosition: finalLandingPoint,
        glideDistance: glideDistanceNM,
        glideTime: timeToGlide / 60, // minutes
        uncertaintyRadius: uncertaintyRadiusMeters / 1000, // km
        heading: heading,
        windEffect: {
            speed: windSpeed,
            direction: windDirection,
            distance: windEffectDistance / 1000 // km
        }
    };
}

/**
 * Generate a circular landing zone with points
 * @param {Array} center - Center point [latitude, longitude] in degrees
 * @param {number} radiusMeters - Radius in meters
 * @param {number} numPoints - Number of points to generate
 * @returns {Array} Array of points forming a circle
 */
function generateLandingZoneCircle(center, radiusMeters, numPoints = 36) {
    const points = [];
    
    for (let i = 0; i <= numPoints; i++) {
        const bearing = (i * 360 / numPoints) % 360;
        const point = calculateDestinationPoint(center, bearing, radiusMeters);
        points.push(point);
    }
    
    return points;
}

/**
 * Convert degrees to radians
 * @param {number} degrees - Angle in degrees
 * @returns {number} Angle in radians
 */
function toRadians(degrees) {
    return degrees * Math.PI / 180;
}

/**
 * Convert radians to degrees
 * @param {number} radians - Angle in radians
 * @returns {number} Angle in degrees
 */
function toDegrees(radians) {
    return radians * 180 / Math.PI;
}

/**
 * Format coordinates for display
 * @param {Array} coords - Coordinates [latitude, longitude] in degrees
 * @returns {string} Formatted coordinates string
 */
function formatCoordinates(coords) {
    if (!coords || coords.length !== 2) return 'Unknown';
    
    const lat = coords[0].toFixed(6);
    const lon = coords[1].toFixed(6);
    const latDir = lat >= 0 ? 'N' : 'S';
    const lonDir = lon >= 0 ? 'E' : 'W';
    
    return `${Math.abs(lat)}° ${latDir}, ${Math.abs(lon)}° ${lonDir}`;
}

/**
 * Format glide distance for display
 * @param {number} distance - Distance in nautical miles
 * @returns {string} Formatted distance string
 */
function formatGlideDistance(distance) {
    if (!distance) return 'Unknown';
    return `${distance.toFixed(1)} NM`;
}

/**
 * Format glide time for display
 * @param {number} time - Time in minutes
 * @returns {string} Formatted time string
 */
function formatGlideTime(time) {
    if (!time) return 'Unknown';
    
    const minutes = Math.floor(time);
    const seconds = Math.round((time - minutes) * 60);
    
    return `${minutes}m ${seconds}s`;
}