// Global variables
let map;
let searchCenter = null;
let searchRadius = null;
let probabilityPoints = null;
let lastPositionMarker = null;
let searchCircle = null;
let heatmapLayer = null;
let highProbMarkers = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Initialize map
    map = L.map('map').setView([37.7749, -122.4194], 8);
    
    // Add base layers
    const openStreetMap = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    const stamenTerrain = L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png', {
        attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    });
    
    const cartoLight = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    });
    
    const cartoDark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    });
    
    // Add layer control
    const baseLayers = {
        "OpenStreetMap": openStreetMap,
        "Terrain": stamenTerrain,
        "Light": cartoLight,
        "Dark": cartoDark
    };
    
    L.control.layers(baseLayers).addTo(map);
    
    // Update aircraft specs when aircraft type changes
    document.getElementById('aircraft-type').addEventListener('change', function(e) {
        updateAircraftSpecs(e.target.value);
    });
    
    // Update range slider displays
    document.getElementById('radius-multiplier').addEventListener('input', function(e) {
        document.getElementById('radius-value').textContent = parseFloat(e.target.value).toFixed(1);
    });
    
    document.getElementById('probability-points').addEventListener('input', function(e) {
        document.getElementById('points-value').textContent = e.target.value;
    });
    
    // Handle the calculate button click
    document.getElementById('calculate-btn').addEventListener('click', calculateSearchArea);
    
    // Handle export button click
    document.getElementById('export-btn').addEventListener('click', exportData);
    
    // Initialize accordion functionality
    initAccordion();
    
    // Initialize with default aircraft specs
    updateAircraftSpecs(document.getElementById('aircraft-type').value);
});

// Initialize accordion functionality
function initAccordion() {
    const accordionItems = document.querySelectorAll('.accordion-item');
    
    accordionItems.forEach(item => {
        const header = item.querySelector('.accordion-header');
        
        header.addEventListener('click', () => {
            // Toggle this item
            item.classList.toggle('active');
            
            // Close other items
            accordionItems.forEach(otherItem => {
                if (otherItem !== item && otherItem.classList.contains('active')) {
                    otherItem.classList.remove('active');
                }
            });
        });
    });
    
    // Open the first accordion by default
    if (accordionItems.length > 0) {
        accordionItems[0].classList.add('active');
    }
}

// Calculate search area and update the map
function calculateSearchArea() {
    // Show loading spinner
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.style.display = 'block';
    document.getElementById('map').appendChild(spinner);
    
    // Get input values
    const latitude = parseFloat(document.getElementById('latitude').value);
    const longitude = parseFloat(document.getElementById('longitude').value);
    const altitude = parseFloat(document.getElementById('altitude').value);
    const groundSpeed = parseFloat(document.getElementById('ground-speed').value);
    const heading = parseFloat(document.getElementById('heading').value);
    const verticalSpeed = parseFloat(document.getElementById('vertical-speed').value);
    const windSpeed = parseFloat(document.getElementById('wind-speed').value);
    const windDirection = parseFloat(document.getElementById('wind-direction').value);
    const searchRadiusMultiplier = parseFloat(document.getElementById('radius-multiplier').value);
    const numPoints = parseInt(document.getElementById('probability-points').value);
    const aircraftType = document.getElementById('aircraft-type').value;
    
    // Get aircraft specifications
    const aircraftSpecs = aircraftTypes[aircraftType];
    
    // Calculate the search area
    setTimeout(() => {
        try {
            const results = calculateSearchArea(
                latitude,
                longitude,
                altitude,
                groundSpeed,
                heading,
                verticalSpeed,
                windSpeed,
                windDirection,
                aircraftSpecs,
                searchRadiusMultiplier
            );
            
            searchCenter = results.searchCenter;
            searchRadius = results.searchRadius;
            const glideDistance = results.glideDistance;
            
            // Generate probability distribution
            probabilityPoints = calculateProbabilityDistribution(
                searchCenter,
                searchRadius,
                numPoints,
                heading,
                windDirection,
                windSpeed,
                glideDistance
            );
            
            // Update the map
            updateMap(latitude, longitude, searchCenter, searchRadius, probabilityPoints);
            
            // Update results display
            updateResultsDisplay(searchCenter, searchRadius, glideDistance);
            
            // Enable export button
            document.getElementById('export-btn').disabled = false;
        } catch (error) {
            console.error("Error calculating search area:", error);
            alert("An error occurred while calculating the search area. Please check your inputs and try again.");
        } finally {
            // Remove spinner
            spinner.remove();
        }
    }, 100); // Small timeout to allow UI to update
}

// Update the map with search results
function updateMap(lastLat, lastLon, searchCenter, searchRadius, probabilityPoints) {
    // Clear previous layers
    if (lastPositionMarker) map.removeLayer(lastPositionMarker);
    if (searchCircle) map.removeLayer(searchCircle);
    if (heatmapLayer) map.removeLayer(heatmapLayer);
    highProbMarkers.forEach(marker => map.removeLayer(marker));
    highProbMarkers = [];
    
    // Add last known position marker
    lastPositionMarker = L.marker([lastLat, lastLon], {
        icon: L.divIcon({
            html: '<i class="fas fa-plane" style="color: blue; font-size: 24px;"></i>',
            iconSize: [24, 24],
            className: 'aircraft-marker'
        })
    }).addTo(map);
    lastPositionMarker.bindPopup("<strong>Last Known Position</strong>");
    
    // Add search radius circle (convert nm to meters)
    searchCircle = L.circle(searchCenter, {
        radius: searchRadius * 1852, // Convert nm to meters
        color: 'blue',
        fillColor: 'blue',
        fillOpacity: 0.1,
        weight: 2
    }).addTo(map);
    searchCircle.bindPopup(`<strong>Search Radius:</strong> ${searchRadius.toFixed(2)} nm`);
    
    // Format heatmap data
    const heatData = probabilityPoints.map(point => {
        return [point[0], point[1], point[2] * 10000]; // Scale for visibility
    });
    
    // Add heatmap layer
    heatmapLayer = L.heatLayer(heatData, {
        radius: 15,
        blur: 10,
        maxZoom: 13,
        gradient: {
            0.2: 'blue',
            0.4: 'lime',
            0.6: 'yellow',
            0.8: 'orange',
            1.0: 'red'
        }
    }).addTo(map);
    
    // Add markers for highest probability points (top 5)
    const sortedPoints = [...probabilityPoints].sort((a, b) => b[2] - a[2]);
    const topPoints = sortedPoints.slice(0, 5);
    
    topPoints.forEach((point, i) => {
        const marker = L.circleMarker([point[0], point[1]], {
            radius: 8,
            color: 'red',
            fillColor: 'red',
            fillOpacity: 0.8,
            weight: 2
        }).addTo(map);
        marker.bindPopup(`<strong>High Probability Area #${i+1}</strong><br>Probability: ${point[2].toFixed(2)}`);
        highProbMarkers.push(marker);
    });
    
    // Center and zoom the map to show the search area
    map.fitBounds(searchCircle.getBounds());
}

// Update the results display
function updateResultsDisplay(searchCenter, searchRadius, glideDistance) {
    const searchArea = Math.PI * searchRadius * searchRadius;
    
    document.getElementById('results-content').innerHTML = `
        <p><strong>Search center:</strong> ${searchCenter[0].toFixed(6)}°N, ${searchCenter[1].toFixed(6)}°E</p>
        <p><strong>Search radius:</strong> ${searchRadius.toFixed(2)} nautical miles</p>
        <p><strong>Maximum glide distance:</strong> ${glideDistance.toFixed(2)} nautical miles</p>
        <p><strong>Total search area:</strong> ${searchArea.toFixed(2)} square nautical miles</p>
    `;
}

// Export the search data
function exportData() {
    if (!searchCenter || !searchRadius || !probabilityPoints) {
        alert("Please calculate search area first.");
        return;
    }
    
    const exportFormat = document.getElementById('export-format').value;
    const data = exportSearchCoordinates(searchCenter, searchRadius, probabilityPoints, exportFormat);
    
    // Create timestamp for filename
    const now = new Date();
    const timestamp = now.getFullYear() + 
                      String(now.getMonth() + 1).padStart(2, '0') + 
                      String(now.getDate()).padStart(2, '0') + '_' +
                      String(now.getHours()).padStart(2, '0') + 
                      String(now.getMinutes()).padStart(2, '0') + 
                      String(now.getSeconds()).padStart(2, '0');
    
    // Create filename
    const filename = `aircraft_search_${timestamp}.${exportFormat === 'csv' ? 'csv' : 'geojson'}`;
    
    // Create download link
    const blob = new Blob([data], { type: exportFormat === 'csv' ? 'text/csv' : 'application/geo+json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
}