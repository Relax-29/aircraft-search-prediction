/**
 * Map Controls Module
 * Handles map initialization and interaction
 */

let map;
let aircraftMarkers = {};
let selectedAircraft = null;
let glidePathLayer = null;
let landingZoneLayer = null;

/**
 * Initialize the map with default settings
 */
function initMap() {
    try {
        console.log("Initializing map...");
        const mapContainer = document.getElementById('map');
        
        if (!mapContainer) {
            console.error("Map container not found!");
            return;
        }
        
        // If map is already initialized, don't recreate it
        if (window.mapInitialized) {
            console.log("Map already initialized");
            return;
        }
        
        // Create map centered on a default location
        console.log("Creating Leaflet map...");
        map = L.map('map').setView([40.7128, -74.0060], 5);
        
        // Add base OSM tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(map);
        
        // Add satellite imagery layer
        const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            maxZoom: 19
        });
        
        // Add terrain layer
        const terrainLayer = L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg', {
            attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18
        });
        
        // Add dark mode layer
        const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            maxZoom: 19
        });
        
        try {
            // Add layer control
            const baseLayers = {
                "Standard": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'), 
                "Satellite": satelliteLayer,
                "Terrain": terrainLayer,
                "Dark Mode": darkLayer
            };
            
            L.control.layers(baseLayers).addTo(map);
            
            // Add scale
            L.control.scale({imperial: true, metric: true}).addTo(map);
            
            // Mark as initialized
            window.mapInitialized = true;
            console.log("Map successfully initialized");
            
            // Show loading indicator
            showLoading();
        } catch (error) {
            console.error("Error adding layers to map:", error);
        }
    } catch (error) {
        console.error("Error initializing map:", error);
    }
}

/**
 * Add an aircraft marker to the map
 * @param {Object} aircraft - Aircraft data object
 * @returns {Object} The created marker
 */
function addAircraftMarker(aircraft) {
    if (!aircraft || !aircraft.icao24 || !aircraft.latitude || !aircraft.longitude) {
        return null;
    }
    
    // Create custom icon with rotation based on heading
    const markerHtml = `<i class="fas fa-plane" style="transform: rotate(${aircraft.true_track || 0}deg);"></i>`;
    const customIcon = L.divIcon({
        html: markerHtml,
        className: 'aircraft-marker',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
    
    // Create tooltip content
    const tooltipContent = createTooltipContent(aircraft);
    
    // Create marker
    const marker = L.marker([aircraft.latitude, aircraft.longitude], {
        icon: customIcon,
        alt: aircraft.icao24
    }).addTo(map);
    
    // Add tooltip
    marker.bindTooltip(tooltipContent, {
        className: 'custom-tooltip',
        direction: 'top',
        offset: [0, -10]
    });
    
    // Add click handler
    marker.on('click', function() {
        selectAircraft(aircraft);
    });
    
    // Store the marker
    aircraftMarkers[aircraft.icao24] = {
        marker: marker,
        data: aircraft
    };
    
    return marker;
}

/**
 * Update an existing aircraft marker
 * @param {Object} aircraft - Updated aircraft data
 */
function updateAircraftMarker(aircraft) {
    if (!aircraft || !aircraft.icao24 || !aircraft.latitude || !aircraft.longitude) {
        return;
    }
    
    const existingMarker = aircraftMarkers[aircraft.icao24];
    
    if (existingMarker) {
        // Update position
        existingMarker.marker.setLatLng([aircraft.latitude, aircraft.longitude]);
        
        // Update rotation if we have heading information
        if (aircraft.true_track !== undefined) {
            const newIcon = L.divIcon({
                html: `<i class="fas fa-plane" style="transform: rotate(${aircraft.true_track}deg);"></i>`,
                className: existingMarker.marker.options.icon.options.className,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });
            
            existingMarker.marker.setIcon(newIcon);
        }
        
        // Update tooltip
        existingMarker.marker.setTooltipContent(createTooltipContent(aircraft));
        
        // Update stored data
        existingMarker.data = aircraft;
        
        // Update info panel if this is the selected aircraft
        if (selectedAircraft && selectedAircraft.icao24 === aircraft.icao24) {
            updateFlightInfoPanel(aircraft);
        }
    } else {
        // If marker doesn't exist, create it
        addAircraftMarker(aircraft);
    }
}

/**
 * Remove an aircraft marker from the map
 * @param {string} icao24 - Aircraft ICAO24 address
 */
function removeAircraftMarker(icao24) {
    if (aircraftMarkers[icao24]) {
        map.removeLayer(aircraftMarkers[icao24].marker);
        delete aircraftMarkers[icao24];
    }
}

/**
 * Create tooltip content for an aircraft marker
 * @param {Object} aircraft - Aircraft data
 * @returns {string} HTML content for tooltip
 */
function createTooltipContent(aircraft) {
    const callsign = aircraft.callsign ? aircraft.callsign.trim() : 'N/A';
    const altitude = aircraft.geo_altitude || aircraft.baro_altitude || 0;
    const speed = aircraft.velocity || 0;
    
    return `
        <h4>${callsign}</h4>
        <p>ICAO: ${aircraft.icao24}</p>
        <p>ALT: ${Math.round(altitude).toLocaleString()} ft</p>
        <p>SPD: ${Math.round(speed)} kts</p>
    `;
}

/**
 * Select an aircraft and show its details
 * @param {Object} aircraft - The aircraft to select
 */
function selectAircraft(aircraft) {
    // Deselect previously selected aircraft
    if (selectedAircraft && aircraftMarkers[selectedAircraft.icao24]) {
        const prevMarker = aircraftMarkers[selectedAircraft.icao24].marker;
        const prevIcon = prevMarker.options.icon;
        
        // Remove selected class
        prevIcon.options.className = 'aircraft-marker';
        prevMarker.setIcon(L.divIcon({
            html: prevIcon.options.html,
            className: 'aircraft-marker',
            iconSize: prevIcon.options.iconSize,
            iconAnchor: prevIcon.options.iconAnchor
        }));
    }
    
    // Set new selected aircraft
    selectedAircraft = aircraft;
    
    // Highlight the selected aircraft marker
    if (aircraftMarkers[aircraft.icao24]) {
        const marker = aircraftMarkers[aircraft.icao24].marker;
        const icon = marker.options.icon;
        
        // Add selected class
        marker.setIcon(L.divIcon({
            html: icon.options.html,
            className: 'aircraft-marker selected',
            iconSize: icon.options.iconSize,
            iconAnchor: icon.options.iconAnchor
        }));
        
        // Pan to the selected aircraft
        map.panTo(marker.getLatLng());
    }
    
    // Update flight info panel
    updateFlightInfoPanel(aircraft);
    
    // Open flight info panel if it's closed
    document.getElementById('flight-info-panel').classList.add('open');
}

/**
 * Display the glide path and landing zone on the map
 * @param {Object} prediction - Prediction data from predictLandingZone
 */
function displayGlidePath(prediction) {
    // Remove existing layers if they exist
    if (glidePathLayer) map.removeLayer(glidePathLayer);
    if (landingZoneLayer) map.removeLayer(landingZoneLayer);
    
    // Create glide path line
    glidePathLayer = L.polyline([
        prediction.aircraftPosition,
        prediction.landingPosition
    ], {
        color: '#f59e0b',
        weight: 3,
        opacity: 0.8,
        dashArray: '10, 10'
    }).addTo(map);
    
    // Add class for animation
    const path = glidePathLayer.getElement();
    if (path) path.classList.add('glide-path');
    
    // Create landing zone circle
    const radiusMeters = prediction.uncertaintyRadius * 1000;
    landingZoneLayer = L.circle(prediction.landingPosition, {
        radius: radiusMeters,
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: 0.2,
        weight: 2
    }).addTo(map);
    
    // Add popup with landing zone info
    landingZoneLayer.bindPopup(`
        <strong>Predicted Landing Zone</strong><br>
        Position: ${formatCoordinates(prediction.landingPosition)}<br>
        Glide Distance: ${formatGlideDistance(prediction.glideDistance)}<br>
        Glide Time: ${formatGlideTime(prediction.glideTime)}<br>
        Uncertainty: ${prediction.uncertaintyRadius.toFixed(1)} km
    `);
    
    // Adjust map view to show both aircraft and landing zone
    const bounds = L.latLngBounds(prediction.aircraftPosition, prediction.landingPosition).pad(0.3);
    map.fitBounds(bounds);
    
    // Show the landing zone popup
    landingZoneLayer.openPopup();
}

/**
 * Clear the current glide path and landing zone display
 */
function clearGlidePrediction() {
    if (glidePathLayer) {
        map.removeLayer(glidePathLayer);
        glidePathLayer = null;
    }
    
    if (landingZoneLayer) {
        map.removeLayer(landingZoneLayer);
        landingZoneLayer = null;
    }
    
    // Hide prediction info in the panel
    document.getElementById('prediction-info').classList.add('hidden');
}

/**
 * Show loading indicator on the map
 */
function showLoading() {
    // Check if loading indicator already exists
    if (document.getElementById('map-loading')) return;
    
    // Create loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'map-loading';
    loadingDiv.className = 'loading-indicator';
    
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    
    const loadingText = document.createElement('div');
    loadingText.textContent = 'Loading aircraft data...';
    
    loadingDiv.appendChild(spinner);
    loadingDiv.appendChild(loadingText);
    
    // Add to map container
    document.getElementById('map-container').appendChild(loadingDiv);
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loadingDiv = document.getElementById('map-loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}