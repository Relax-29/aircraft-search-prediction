// Utility functions for calculations
function toRadians(degrees) {
    return degrees * Math.PI / 180;
}

function toDegrees(radians) {
    return radians * 180 / Math.PI;
}

// Haversine distance function - calculates distance between two coordinates in nautical miles
function haversineDistance(lat1, lon1, lat2, lon2) {
    // Convert decimal degrees to radians
    lat1 = toRadians(lat1);
    lon1 = toRadians(lon1);
    lat2 = toRadians(lat2);
    lon2 = toRadians(lon2);
    
    // Haversine formula
    const dlon = lon2 - lon1;
    const dlat = lat2 - lat1;
    const a = Math.sin(dlat/2)**2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon/2)**2;
    const c = 2 * Math.asin(Math.sqrt(a));
    
    // Radius of earth in nautical miles
    const r = 3440.065;
    
    return c * r;
}

// Calculate bearing between two points
function calculateBearing(lat1, lon1, lat2, lon2) {
    // Convert decimal degrees to radians
    lat1 = toRadians(lat1);
    lon1 = toRadians(lon1);
    lat2 = toRadians(lat2);
    lon2 = toRadians(lon2);
    
    // Calculate bearing
    const dlon = lon2 - lon1;
    const y = Math.sin(dlon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dlon);
    
    let bearing = Math.atan2(y, x);
    
    // Convert to degrees
    bearing = toDegrees(bearing);
    
    // Normalize to 0-360
    bearing = (bearing + 360) % 360;
    
    return bearing;
}

// Get destination point given starting point, bearing, and distance
function getDestinationPoint(lat, lon, bearing, distance) {
    // Convert decimal degrees to radians
    lat = toRadians(lat);
    lon = toRadians(lon);
    bearing = toRadians(bearing);
    
    // Earth radius in nautical miles
    const earthRadius = 3440.065;
    
    // Calculate destination point
    const lat2 = Math.asin(Math.sin(lat) * Math.cos(distance/earthRadius) + 
                     Math.cos(lat) * Math.sin(distance/earthRadius) * Math.cos(bearing));
    
    const lon2 = lon + Math.atan2(Math.sin(bearing) * Math.sin(distance/earthRadius) * Math.cos(lat),
                           Math.cos(distance/earthRadius) - Math.sin(lat) * Math.sin(lat2));
    
    // Convert back to degrees
    return [toDegrees(lat2), toDegrees(lon2)];
}

// Calculate search area based on last known position and flight parameters
function calculateSearchArea(latitude, longitude, altitude, groundSpeed, heading, 
                           verticalSpeed, windSpeed, windDirection, aircraftSpecs, searchRadiusMultiplier) {
    // Convert altitude from feet to nautical miles (1 nm = 6076 feet)
    const altitudeNm = altitude / 6076;
    
    // Calculate maximum glide distance based on glide ratio and altitude
    const glideDistance = altitudeNm * aircraftSpecs.glide_ratio;
    
    // Calculate time to impact based on vertical speed (minutes)
    // If vertical speed is zero or positive, use a conservative estimate based on emergency descent rate
    let timeToImpactMinutes;
    if (verticalSpeed <= 0) {
        timeToImpactMinutes = verticalSpeed < 0 ? altitude / Math.abs(verticalSpeed) : altitude / aircraftSpecs.emergency_descent_rate;
    } else {
        // If climbing, assume emergency and use emergency descent rate
        timeToImpactMinutes = altitude / aircraftSpecs.emergency_descent_rate;
    }
    
    // Convert time to hours
    const timeToImpactHours = timeToImpactMinutes / 60;
    
    // Calculate horizontal distance traveled during descent (nautical miles)
    const horizontalDistance = groundSpeed * timeToImpactHours;
    
    // Calculate the initial search center based on heading and horizontal distance
    const [initialCenterLat, initialCenterLon] = getDestinationPoint(
        latitude, longitude, heading, horizontalDistance);
    
    // Adjust for wind effect
    // Calculate wind effect distance (wind speed * time to impact)
    const windDistance = windSpeed * timeToImpactHours;
    
    // Calculate the final search center with wind adjustment
    const [finalCenterLat, finalCenterLon] = getDestinationPoint(
        initialCenterLat, initialCenterLon, windDirection, windDistance);
    
    // Calculate search radius:
    // Base radius on the larger of glide distance or horizontal distance traveled
    const baseRadius = Math.max(glideDistance, horizontalDistance);
    
    // Add uncertainty based on wind
    const windUncertainty = windDistance * 0.2;  // 20% of wind distance
    
    // Apply search radius multiplier for safety margin
    const searchRadius = (baseRadius + windUncertainty) * searchRadiusMultiplier;
    
    return {
        searchCenter: [finalCenterLat, finalCenterLon],
        searchRadius: searchRadius,
        glideDistance: glideDistance
    };
}

// Random number from normal distribution
function randn() {
    let u = 0, v = 0;
    while(u === 0) u = Math.random();
    while(v === 0) v = Math.random();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// Generate a random number from a von Mises distribution (circular normal)
function vonMises(mu, kappa) {
    // For kappa = 0, return uniform distribution
    if (kappa === 0) {
        return 2 * Math.PI * Math.random() - Math.PI;
    }
    
    // For small kappa, use normal approximation with correction
    const a = 1 + Math.sqrt(1 + 4 * kappa * kappa);
    const b = (a - Math.sqrt(2 * a)) / (2 * kappa);
    const r = (1 + b * b) / (2 * b);
    
    let u1, u2, u3, z, f, c;
    
    while (true) {
        u1 = Math.random();
        z = Math.cos(Math.PI * u1);
        f = (1 + r * z) / (r + z);
        c = kappa * (r - f);
        
        u2 = Math.random();
        if (u2 <= c * (2 - c) || u2 <= c * Math.exp(1 - c)) {
            u3 = Math.random();
            return (u3 > 0.5 ? 1 : -1) * Math.acos(f) + mu;
        }
    }
}

// Generate probability distribution for the search area
function calculateProbabilityDistribution(searchCenter, searchRadius, numPoints, heading, 
                                        windDirection, windSpeed, glideDistance) {
    // Convert degrees to radians for calculations
    const headingRad = toRadians(heading);
    const windDirectionRad = toRadians(windDirection);
    
    // Calculate the direction of highest probability (combination of heading and wind direction)
    // Weight heading and wind direction based on wind speed (higher wind = higher weight)
    const windWeight = Math.min(windSpeed / 50, 0.8);  // cap at 80%
    const headingWeight = 1 - windWeight;
    
    // Convert heading and wind direction to x,y components
    const headingX = Math.cos(headingRad);
    const headingY = Math.sin(headingRad);
    const windX = Math.cos(windDirectionRad);
    const windY = Math.sin(windDirectionRad);
    
    // Calculate the weighted direction
    const directionX = headingWeight * headingX + windWeight * windX;
    const directionY = headingWeight * headingY + windWeight * windY;
    
    // Convert back to angle
    const highProbDirection = Math.atan2(directionY, directionX);
    
    // Generate random points with higher concentration in the direction of travel and wind
    const results = [];
    const centerLat = searchCenter[0];
    const centerLon = searchCenter[1];
    
    for (let i = 0; i < numPoints; i++) {
        // Generate a random distance using a Rayleigh distribution (distance from center)
        const rand = Math.random();
        const distance = Math.min(
            searchRadius * Math.sqrt(-2 * Math.log(rand)), 
            searchRadius
        );
        
        // Generate a random angle with bias toward the high probability direction
        const kappa = 2.0; // Concentration parameter
        const angle = vonMises(highProbDirection, kappa);
        
        // Convert polar coordinates to Cartesian
        const x = distance * Math.cos(angle);
        const y = distance * Math.sin(angle);
        
        // Calculate probability based on distance from center and alignment
        const maxDistance = searchRadius;
        const distanceFromCenter = Math.sqrt(x**2 + y**2);
        
        // Calculate the angle difference between point and high probability direction
        let angleDiff = Math.abs(Math.atan2(y, x) - highProbDirection);
        angleDiff = Math.min(angleDiff, 2*Math.PI - angleDiff); // Ensure the difference is the smaller angle
        
        // Calculate probability based on distance and angle
        // Exponential decay with distance from center
        const distanceFactor = Math.exp(-1.5 * distanceFromCenter / maxDistance);
        // Cosine factor for angle
        const angleFactor = Math.cos(angleDiff)**2;
        
        // Combine factors into final probability
        const probability = distanceFactor * (0.7 + 0.3 * angleFactor);
        
        // Convert x,y offsets to lat/lon points
        const earthRadiusNm = 3440.065;  // Earth radius in nautical miles
        const latPoint = centerLat + toDegrees(y / earthRadiusNm);
        const lonPoint = centerLon + toDegrees(x / (earthRadiusNm * Math.cos(toRadians(centerLat))));
        
        // Add to results
        results.push([latPoint, lonPoint, probability]);
    }
    
    // Normalize probabilities
    const maxProb = results.reduce((max, point) => Math.max(max, point[2]), 0);
    results.forEach(point => {
        point[2] = point[2] / maxProb;
    });
    
    return results;
}

// Export search coordinates to CSV or GeoJSON
function exportSearchCoordinates(searchCenter, searchRadius, probabilityPoints, exportFormat) {
    if (exportFormat === "csv") {
        // Create CSV content
        let csv = "Latitude,Longitude,Probability,Type\n";
        
        // Add search center
        csv += `${searchCenter[0]},${searchCenter[1]},1.0,center\n`;
        
        // Add search area boundary points
        const numBoundaryPoints = 36;  // One point every 10 degrees
        for (let i = 0; i < numBoundaryPoints; i++) {
            const angle = toRadians(i * 10);
            const [lat, lon] = getDestinationPoint(searchCenter[0], searchCenter[1], 
                                              toDegrees(angle), searchRadius);
            csv += `${lat},${lon},0.0,boundary\n`;
        }
        
        // Add probability points (only include significant points)
        const significantPoints = probabilityPoints.filter(p => p[2] > 0.2);
        for (const point of significantPoints) {
            csv += `${point[0]},${point[1]},${point[2]},probability\n`;
        }
        
        return csv;
        
    } else {  // GeoJSON
        const features = [];
        
        // Add search center
        features.push({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [searchCenter[1], searchCenter[0]]  // GeoJSON uses [lon, lat]
            },
            "properties": {
                "type": "center",
                "probability": 1.0,
                "description": "Search Area Center"
            }
        });
        
        // Add search area boundary
        const boundaryCoords = [];
        const numBoundaryPoints = 36;  // One point every 10 degrees
        for (let i = 0; i <= numBoundaryPoints; i++) {  // +1 to close the loop
            const angle = toRadians(i % 36 * 10);
            const [lat, lon] = getDestinationPoint(searchCenter[0], searchCenter[1], 
                                              toDegrees(angle), searchRadius);
            boundaryCoords.push([lon, lat]);  // GeoJSON uses [lon, lat]
        }
        
        features.push({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [boundaryCoords]
            },
            "properties": {
                "type": "boundary",
                "description": `Search Area Boundary (${searchRadius.toFixed(2)} nm radius)`
            }
        });
        
        // Add high probability points
        const highProbPoints = probabilityPoints.filter(p => p[2] > 0.5);
        for (const point of highProbPoints) {
            features.push({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point[1], point[0]]  // GeoJSON uses [lon, lat]
                },
                "properties": {
                    "type": "probability",
                    "probability": point[2],
                    "description": `Probability: ${point[2].toFixed(2)}`
                }
            });
        }
        
        // Create GeoJSON object
        const geojson = {
            "type": "FeatureCollection",
            "features": features
        };
        
        return JSON.stringify(geojson, null, 2);
    }
}