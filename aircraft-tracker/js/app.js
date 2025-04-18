/**
 * Main Application Script
 * Handles UI interactions and API communication
 */

// Global variables
let isLiveTracking = false;
let pollingInterval = null;
const OPENSKY_API_URL = 'https://opensky-network.org/api/states/all';
const POLLING_INTERVAL_MS = 10000; // 10 seconds between updates

// DOM elements
const connectionStatus = document.getElementById('connection-status');
const liveTrackingBtn = document.getElementById('live-tracking-btn');
const searchBtn = document.getElementById('search-btn');
const searchTypeSelect = document.getElementById('search-type');
const searchValueInput = document.getElementById('search-value');
const calculateGlideBtn = document.getElementById('calculate-glide-btn');
const aircraftTypeSelect = document.getElementById('aircraft-type');
const windSpeedInput = document.getElementById('wind-speed');
const windDirectionInput = document.getElementById('wind-direction');
const closeInfoPanelBtn = document.getElementById('close-info-panel');
const helpBtn = document.getElementById('help-btn');
const closeHelpModalBtn = document.getElementById('close-help-modal');
const helpModal = document.getElementById('help-modal');
const flightInfoPanel = document.getElementById('flight-info-panel');

/**
 * Initialize the application
 */
function initApp() {
    console.log("Initializing aircraft tracker application...");
    
    // Wrap in timeout to ensure DOM is fully loaded in iframe context
    setTimeout(() => {
        try {
            // Re-acquire DOM elements to ensure they're available
            const connectionStatus = document.getElementById('connection-status');
            const liveTrackingBtn = document.getElementById('live-tracking-btn');
            const searchBtn = document.getElementById('search-btn');
            const calculateGlideBtn = document.getElementById('calculate-glide-btn');
            const closeInfoPanelBtn = document.getElementById('close-info-panel');
            const helpBtn = document.getElementById('help-btn');
            const closeHelpModalBtn = document.getElementById('close-help-modal');
            
            // Check critical elements
            if (!document.getElementById('map')) {
                console.error("Map container not found!");
                return;
            }
            
            // Initialize map
            console.log("Initializing map...");
            initMap();
            console.log("Map initialized");
            
            // Set up event listeners with error handling
            if (liveTrackingBtn) {
                liveTrackingBtn.addEventListener('click', toggleLiveTracking);
                console.log("Live tracking button listener attached");
            } else {
                console.error("Live tracking button not found!");
            }
            
            if (searchBtn) {
                searchBtn.addEventListener('click', searchAircraft);
                console.log("Search button listener attached");
            }
            
            if (calculateGlideBtn) {
                calculateGlideBtn.addEventListener('click', calculateGlidePrediction);
                console.log("Calculate glide button listener attached");
            }
            
            if (closeInfoPanelBtn) {
                closeInfoPanelBtn.addEventListener('click', closeFlightInfoPanel);
                console.log("Close info panel button listener attached");
            }
            
            if (helpBtn) {
                helpBtn.addEventListener('click', showHelp);
                console.log("Help button listener attached");
            }
            
            if (closeHelpModalBtn) {
                closeHelpModalBtn.addEventListener('click', hideHelp);
                console.log("Close help modal button listener attached");
            }
            
            // Start with sample aircraft data
            console.log("Loading sample aircraft data...");
            fetchSampleData();
            console.log("Application initialization complete");
            
        } catch (error) {
            console.error("Error during application initialization:", error);
        }
    }, 1000);
}

/**
 * Toggle live tracking on/off
 */
function toggleLiveTracking() {
    isLiveTracking = !isLiveTracking;
    
    if (isLiveTracking) {
        // Start tracking
        connectionStatus.className = 'inline-block w-2 h-2 rounded-full bg-yellow-500 mr-2';
        connectionStatus.classList.add('connecting');
        liveTrackingBtn.textContent = 'Stop Tracking';
        liveTrackingBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
        liveTrackingBtn.classList.add('bg-red-600', 'hover:bg-red-700');
        
        // Fetch initial data and set up polling
        fetchLiveAircraftData();
        pollingInterval = setInterval(fetchLiveAircraftData, POLLING_INTERVAL_MS);
    } else {
        // Stop tracking
        connectionStatus.className = 'inline-block w-2 h-2 rounded-full bg-red-500 mr-2';
        connectionStatus.classList.remove('connecting');
        liveTrackingBtn.textContent = 'Live Tracking';
        liveTrackingBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
        liveTrackingBtn.classList.add('bg-green-600', 'hover:bg-green-700');
        
        // Clear interval
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }
}

/**
 * Fetch live aircraft data from OpenSky Network API
 */
function fetchLiveAircraftData() {
    // Show loading
    showLoading();
    
    // Determine the bounding box based on current map view
    const bounds = map.getBounds();
    const params = new URLSearchParams({
        lamin: bounds.getSouth(),
        lomin: bounds.getWest(),
        lamax: bounds.getNorth(),
        lomax: bounds.getEast()
    });
    
    fetch(`${OPENSKY_API_URL}?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => processAircraftData(data))
        .catch(error => {
            console.error('Error fetching aircraft data:', error);
            
            // Show error status
            connectionStatus.className = 'inline-block w-2 h-2 rounded-full bg-red-500 mr-2';
            hideLoading();
            
            // Fallback to sample data if API fails
            fetchSampleData();
            
            // If still in tracking mode, try again later
            if (isLiveTracking) {
                setTimeout(() => {
                    connectionStatus.className = 'inline-block w-2 h-2 rounded-full bg-yellow-500 mr-2';
                    connectionStatus.classList.add('connecting');
                }, 2000);
            }
        });
}

/**
 * Process raw aircraft data from API
 * @param {Object} data - Raw data from OpenSky API
 */
function processAircraftData(data) {
    // Hide loading
    hideLoading();
    
    if (!data || !data.states || !Array.isArray(data.states)) {
        console.error('Invalid data format received');
        return;
    }
    
    // Set connected status
    connectionStatus.className = 'inline-block w-2 h-2 rounded-full bg-green-500 mr-2';
    connectionStatus.classList.add('connected');
    
    // Track which aircraft we've seen in this update
    const seenAircraft = new Set();
    
    // Process each aircraft
    data.states.forEach(state => {
        // OpenSky data format: [icao24, callsign, origin_country, time_position, last_contact, longitude, latitude, ...]
        if (!state[0] || !state[5] || !state[6]) return; // Skip if missing essential data
        
        const aircraft = {
            icao24: state[0],
            callsign: state[1] ? state[1].trim() : '',
            origin_country: state[2],
            time_position: state[3],
            last_contact: state[4],
            longitude: state[5],
            latitude: state[6],
            baro_altitude: state[7], // in meters, convert to feet
            on_ground: state[8],
            velocity: state[9], // in m/s, convert to knots
            true_track: state[10], // in degrees
            vertical_rate: state[11], // in m/s, convert to feet/min
            geo_altitude: state[13], // geometric altitude in meters
            squawk: state[14],
            position_source: state[16]
        };
        
        // Convert units
        if (aircraft.baro_altitude) aircraft.baro_altitude = aircraft.baro_altitude * 3.28084;
        if (aircraft.geo_altitude) aircraft.geo_altitude = aircraft.geo_altitude * 3.28084;
        if (aircraft.velocity) aircraft.velocity = aircraft.velocity * 1.94384; // m/s to knots
        if (aircraft.vertical_rate) aircraft.vertical_rate = aircraft.vertical_rate * 196.85; // m/s to ft/min
        
        // Add or update marker on map
        if (aircraftMarkers[aircraft.icao24]) {
            updateAircraftMarker(aircraft);
        } else {
            addAircraftMarker(aircraft);
        }
        
        // Mark as seen
        seenAircraft.add(aircraft.icao24);
    });
    
    // Remove aircraft that are no longer visible
    Object.keys(aircraftMarkers).forEach(icao24 => {
        if (!seenAircraft.has(icao24)) {
            removeAircraftMarker(icao24);
            
            // Clear selected aircraft if it was removed
            if (selectedAircraft && selectedAircraft.icao24 === icao24) {
                selectedAircraft = null;
                closeFlightInfoPanel();
            }
        }
    });
}

/**
 * Search for aircraft based on user input
 */
function searchAircraft() {
    const searchType = searchTypeSelect.value;
    const searchValue = searchValueInput.value.trim();
    
    if (!searchValue) {
        alert('Please enter a search value');
        return;
    }
    
    // Clear any previous highlighting
    Object.values(aircraftMarkers).forEach(item => {
        const marker = item.marker;
        const icon = marker.options.icon;
        
        if (icon.options.className.includes('selected') && item.data.icao24 !== (selectedAircraft?.icao24 || '')) {
            marker.setIcon(L.divIcon({
                html: icon.options.html,
                className: 'aircraft-marker',
                iconSize: icon.options.iconSize,
                iconAnchor: icon.options.iconAnchor
            }));
        }
    });
    
    // Perform search
    let found = false;
    
    Object.values(aircraftMarkers).forEach(item => {
        const aircraft = item.data;
        
        let isMatch = false;
        switch (searchType) {
            case 'callsign':
                isMatch = aircraft.callsign && aircraft.callsign.toLowerCase().includes(searchValue.toLowerCase());
                break;
            case 'icao24':
                isMatch = aircraft.icao24 && aircraft.icao24.toLowerCase().includes(searchValue.toLowerCase());
                break;
            case 'country':
                isMatch = aircraft.origin_country && 
                         aircraft.origin_country.toLowerCase().includes(searchValue.toLowerCase());
                break;
        }
        
        if (isMatch) {
            // Select the first matching aircraft
            if (!found) {
                selectAircraft(aircraft);
                found = true;
            }
        }
    });
    
    if (!found) {
        alert(`No aircraft found matching ${searchType}: ${searchValue}`);
    }
}

/**
 * Update the flight information panel with aircraft data
 * @param {Object} aircraft - Aircraft data object
 */
function updateFlightInfoPanel(aircraft) {
    // Flight callsign/ID
    document.getElementById('flight-callsign').textContent = aircraft.callsign || aircraft.icao24;
    
    // Determine aircraft type
    const estimatedType = estimateAircraftType(aircraft.icao24, aircraft.callsign);
    const aircraftTypeSpec = getAircraftSpecs(estimatedType);
    document.getElementById('flight-aircraft').textContent = 
        `${aircraftTypeSpec.name} (${aircraft.origin_country || 'Unknown'})`;
    
    // Set select box to match estimated aircraft
    if (aircraftTypeSelect) {
        aircraftTypeSelect.value = estimatedType;
    }
    
    // Flight metrics
    const altitude = aircraft.geo_altitude || aircraft.baro_altitude || 0;
    document.getElementById('flight-altitude').textContent = formatAltitude(altitude);
    document.getElementById('flight-speed').textContent = formatGroundSpeed(aircraft.velocity);
    document.getElementById('flight-heading').textContent = formatHeading(aircraft.true_track);
    document.getElementById('flight-vertical-rate').textContent = formatVerticalRate(aircraft.vertical_rate);
    
    // Position
    document.getElementById('flight-position').textContent = 
        formatCoordinates([aircraft.latitude, aircraft.longitude]);
    
    // Hide prediction info initially
    document.getElementById('prediction-info').classList.add('hidden');
}

/**
 * Calculate glide prediction for selected aircraft
 */
function calculateGlidePrediction() {
    if (!selectedAircraft) {
        alert('Please select an aircraft first');
        return;
    }
    
    // Get aircraft type and wind data
    const aircraftType = aircraftTypeSelect.value;
    const aircraftSpecs = getAircraftSpecs(aircraftType);
    const windSpeed = parseFloat(windSpeedInput.value) || 0;
    const windDirection = parseFloat(windDirectionInput.value) || 0;
    
    // Calculate prediction
    const prediction = predictLandingZone(
        selectedAircraft, 
        aircraftSpecs, 
        {speed: windSpeed, direction: windDirection}
    );
    
    // Display on map
    displayGlidePath(prediction);
    
    // Show in info panel
    document.getElementById('prediction-info').classList.remove('hidden');
    document.getElementById('glide-distance').textContent = formatGlideDistance(prediction.glideDistance);
    document.getElementById('landing-coordinates').textContent = formatCoordinates(prediction.landingPosition);
}

/**
 * Close flight information panel
 */
function closeFlightInfoPanel() {
    // Hide the panel
    flightInfoPanel.classList.remove('open');
    
    // Clear selected aircraft highlighting
    if (selectedAircraft && aircraftMarkers[selectedAircraft.icao24]) {
        const marker = aircraftMarkers[selectedAircraft.icao24].marker;
        const icon = marker.options.icon;
        
        marker.setIcon(L.divIcon({
            html: icon.options.html,
            className: 'aircraft-marker',
            iconSize: icon.options.iconSize,
            iconAnchor: icon.options.iconAnchor
        }));
    }
    
    // Clear glide prediction
    clearGlidePrediction();
    
    // Reset selected aircraft
    selectedAircraft = null;
}

/**
 * Show help modal
 */
function showHelp() {
    helpModal.classList.remove('hidden');
}

/**
 * Hide help modal
 */
function hideHelp() {
    helpModal.classList.add('hidden');
}

/**
 * Fetch sample aircraft data when API is not available
 */
function fetchSampleData() {
    // Sample aircraft data for demonstration when API is not available
    const sampleAircraft = [
        {
            icao24: 'a808c5',
            callsign: 'AAL1234',
            origin_country: 'United States',
            latitude: 40.7128,
            longitude: -74.0060,
            baro_altitude: 35000,
            geo_altitude: 35100,
            velocity: 450,
            true_track: 90,
            vertical_rate: 0,
            on_ground: false
        },
        {
            icao24: 'aa8d67',
            callsign: 'DAL2946',
            origin_country: 'United States',
            latitude: 40.8,
            longitude: -73.9,
            baro_altitude: 28000,
            geo_altitude: 28050,
            velocity: 430,
            true_track: 270,
            vertical_rate: -500,
            on_ground: false
        },
        {
            icao24: '4ca748',
            callsign: 'UAL557',
            origin_country: 'United States',
            latitude: 40.65,
            longitude: -73.78,
            baro_altitude: 10000,
            geo_altitude: 10100,
            velocity: 310,
            true_track: 180,
            vertical_rate: -1500,
            on_ground: false
        },
        {
            icao24: 'e76452',
            callsign: 'BAW178',
            origin_country: 'United Kingdom',
            latitude: 40.95,
            longitude: -74.2,
            baro_altitude: 40000,
            geo_altitude: 40100,
            velocity: 490,
            true_track: 45,
            vertical_rate: 0,
            on_ground: false
        }
    ];
    
    // Process sample data
    sampleAircraft.forEach(aircraft => {
        if (aircraftMarkers[aircraft.icao24]) {
            updateAircraftMarker(aircraft);
        } else {
            addAircraftMarker(aircraft);
        }
        
        // Save to database
        saveAircraftToDatabase(aircraft);
    });
    
    // Hide loading
    hideLoading();
}

/**
 * Save aircraft data to the database
 * @param {Object} aircraft - Aircraft data object
 */
function saveAircraftToDatabase(aircraft) {
    // Check if we have the required data
    if (!aircraft || !aircraft.icao24) return;
    
    // Prepare data for the API
    const data = {
        icao24: aircraft.icao24,
        callsign: aircraft.callsign,
        aircraft_type: estimateAircraftType(aircraft.icao24, aircraft.callsign),
        origin_country: aircraft.origin_country
    };
    
    // Make API call to save aircraft
    fetch('http://localhost:5001/api/aircraft', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log(`Aircraft ${aircraft.icao24} saved with ID: ${result.aircraft_id}`);
            
            // Save position if we have it
            if (aircraft.latitude && aircraft.longitude) {
                savePositionToDatabase(result.aircraft_id, aircraft);
            }
        } else {
            console.error(`Error saving aircraft: ${result.error}`);
        }
    })
    .catch(error => {
        console.error('API error saving aircraft:', error);
    });
}

/**
 * Save aircraft position to the database
 * @param {number} aircraft_id - Database ID of the aircraft
 * @param {Object} aircraft - Aircraft data with position
 */
function savePositionToDatabase(aircraft_id, aircraft) {
    // Check if we have position data
    if (!aircraft || !aircraft.latitude || !aircraft.longitude) return;
    
    // Prepare position data
    const positionData = {
        aircraft_id: aircraft_id,
        latitude: aircraft.latitude,
        longitude: aircraft.longitude,
        altitude: aircraft.geo_altitude || aircraft.baro_altitude,
        ground_speed: aircraft.velocity,
        heading: aircraft.true_track,
        vertical_speed: aircraft.vertical_rate,
        on_ground: aircraft.on_ground || false
    };
    
    // Make API call to save position
    fetch('http://localhost:5001/api/positions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(positionData)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log(`Position saved for aircraft ${aircraft_id}, position ID: ${result.position_id}`);
        } else {
            console.error(`Error saving position: ${result.error}`);
        }
    })
    .catch(error => {
        console.error('API error saving position:', error);
    });
}

/**
 * Save search to the database
 * @param {string} searchType - Type of search (callsign, icao24, country)
 * @param {string} searchValue - Value being searched for
 * @param {Array} aircraftIds - IDs of aircraft found
 */
function saveSearchToDatabase(searchType, searchValue, aircraftIds = []) {
    // Prepare search data
    const searchData = {
        search_type: searchType,
        search_value: searchValue,
        aircraft_ids: aircraftIds
    };
    
    // Make API call to save search
    fetch('http://localhost:5001/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(searchData)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log(`Search saved with ID: ${result.query_id}`);
        } else {
            console.error(`Error saving search: ${result.error}`);
        }
    })
    .catch(error => {
        console.error('API error saving search:', error);
    });
}

/**
 * Save emergency prediction to the database
 * @param {Object} aircraft - Aircraft data
 * @param {Object} prediction - Prediction results
 * @param {Object} params - Prediction parameters
 */
function savePredictionToDatabase(aircraft, prediction, params) {
    // First save or update aircraft to get ID
    fetch('http://localhost:5001/api/aircraft', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            icao24: aircraft.icao24,
            callsign: aircraft.callsign,
            aircraft_type: aircraft.aircraft_type || '',
            origin_country: aircraft.origin_country || ''
        })
    })
        .then(response => response.json())
        .then(result => {
            if (!result.success) {
                throw new Error(`Failed to save aircraft: ${result.error}`);
            }
            
            const aircraft_id = result.aircraft_id;
            
            // Prepare prediction data
            const predictionData = {
                aircraft_id: aircraft_id,
                current_position: {
                    latitude: aircraft.latitude,
                    longitude: aircraft.longitude,
                    altitude: aircraft.geo_altitude || aircraft.baro_altitude || 0
                },
                aircraft_params: {
                    ground_speed: aircraft.velocity,
                    heading: aircraft.true_track,
                    vertical_speed: aircraft.vertical_rate
                },
                wind_conditions: {
                    speed: params.windSpeed,
                    direction: params.windDirection
                },
                aircraft_type: params.aircraftType,
                glide_ratio: params.glideRatio,
                prediction_results: prediction
            };
            
            // Make API call to save prediction
            return fetch('http://localhost:5001/api/predictions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(predictionData)
            });
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                console.log(`Prediction saved with ID: ${result.prediction_id}`);
            } else {
                console.error(`Error saving prediction: ${result.error}`);
            }
        })
        .catch(error => {
            console.error('API error saving prediction:', error);
        });
}

// Initialize app when the DOM is ready
document.addEventListener('DOMContentLoaded', initApp);