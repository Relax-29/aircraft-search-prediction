"""
API for connecting the frontend to the database
"""

import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from db_utils import (
    create_or_update_aircraft, store_aircraft_position, 
    store_search_query, store_search_result, store_emergency_prediction,
    get_recent_aircraft, get_aircraft_positions, get_search_history,
    get_prediction_history, find_aircraft_by_callsign,
    find_aircraft_by_icao24, find_aircraft_by_country,
    get_aircraft_by_id
)

app = Flask(__name__)
CORS(app)

@app.route('/api/aircraft', methods=['POST'])
def add_update_aircraft():
    """API endpoint to add or update aircraft"""
    data = request.json
    
    try:
        aircraft_data = create_or_update_aircraft(
            icao24=data['icao24'],
            callsign=data.get('callsign'),
            aircraft_type=data.get('aircraft_type'),
            origin_country=data.get('origin_country')
        )
        
        return jsonify({
            'success': True,
            'aircraft_id': aircraft_data['id']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/positions', methods=['POST'])
def add_position():
    """API endpoint to add aircraft position"""
    data = request.json
    
    try:
        position = store_aircraft_position(
            aircraft_id=data['aircraft_id'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            altitude=data.get('altitude'),
            ground_speed=data.get('ground_speed'),
            heading=data.get('heading'),
            vertical_speed=data.get('vertical_speed'),
            on_ground=data.get('on_ground', False)
        )
        
        return jsonify({
            'success': True,
            'position_id': position.id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    """API endpoint to record a search"""
    data = request.json
    
    try:
        query = store_search_query(
            search_type=data['search_type'],
            search_value=data['search_value']
        )
        
        # Store results if provided
        results = []
        if 'aircraft_ids' in data:
            for aircraft_id in data['aircraft_ids']:
                result = store_search_result(
                    query_id=query.id,
                    aircraft_id=aircraft_id
                )
                results.append(result.id)
        
        return jsonify({
            'success': True,
            'query_id': query.id,
            'result_ids': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictions', methods=['POST'])
def add_prediction():
    """API endpoint to add emergency prediction"""
    data = request.json
    
    try:
        prediction = store_emergency_prediction(
            aircraft_id=data['aircraft_id'],
            current_position=data['current_position'],
            aircraft_params=data['aircraft_params'],
            wind_conditions=data['wind_conditions'],
            aircraft_type=data['aircraft_type'],
            glide_ratio=data['glide_ratio'],
            prediction_results=data['prediction_results']
        )
        
        return jsonify({
            'success': True,
            'prediction_id': prediction.id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/aircraft/recent', methods=['GET'])
def recent_aircraft():
    """API endpoint to get recent aircraft"""
    limit = request.args.get('limit', 100, type=int)
    
    try:
        aircraft_list = get_recent_aircraft(limit=limit)
        
        return jsonify({
            'success': True,
            'aircraft': [{
                'id': a.id,
                'icao24': a.icao24,
                'callsign': a.callsign,
                'aircraft_type': a.aircraft_type,
                'origin_country': a.origin_country,
                'last_updated': a.last_updated.isoformat() if a.last_updated else None
            } for a in aircraft_list]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/aircraft/<int:aircraft_id>/positions', methods=['GET'])
def aircraft_positions(aircraft_id):
    """API endpoint to get positions for an aircraft"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        positions = get_aircraft_positions(aircraft_id=aircraft_id, limit=limit)
        
        return jsonify({
            'success': True,
            'positions': [{
                'id': p.id,
                'timestamp': p.timestamp.isoformat() if p.timestamp else None,
                'latitude': p.latitude,
                'longitude': p.longitude,
                'altitude': p.altitude,
                'ground_speed': p.ground_speed,
                'heading': p.heading,
                'vertical_speed': p.vertical_speed,
                'on_ground': p.on_ground
            } for p in positions]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search/history', methods=['GET'])
def search_history():
    """API endpoint to get search history"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        queries = get_search_history(limit=limit)
        
        return jsonify({
            'success': True,
            'searches': [{
                'id': q.id,
                'search_type': q.search_type,
                'search_value': q.search_value,
                'timestamp': q.timestamp.isoformat() if q.timestamp else None
            } for q in queries]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictions/history', methods=['GET'])
def prediction_history():
    """API endpoint to get prediction history"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        predictions = get_prediction_history(limit=limit)
        
        return jsonify({
            'success': True,
            'predictions': [{
                'id': p.id,
                'aircraft_id': p.aircraft_id,
                'timestamp': p.timestamp.isoformat() if p.timestamp else None,
                'latitude': p.latitude,
                'longitude': p.longitude,
                'altitude': p.altitude,
                'predicted_landing_latitude': p.predicted_landing_latitude,
                'predicted_landing_longitude': p.predicted_landing_longitude,
                'glide_distance': p.glide_distance,
                'glide_time': p.glide_time,
                'aircraft_type': p.aircraft_type
            } for p in predictions]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/aircraft/search/callsign/<callsign>', methods=['GET'])
def search_by_callsign(callsign):
    """API endpoint to search aircraft by callsign"""
    try:
        aircraft_list = find_aircraft_by_callsign(callsign)
        
        return jsonify({
            'success': True,
            'aircraft': [{
                'id': a.id,
                'icao24': a.icao24,
                'callsign': a.callsign,
                'aircraft_type': a.aircraft_type,
                'origin_country': a.origin_country,
                'last_updated': a.last_updated.isoformat() if a.last_updated else None
            } for a in aircraft_list]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/aircraft/search/icao24/<icao24>', methods=['GET'])
def search_by_icao24(icao24):
    """API endpoint to search aircraft by ICAO24 address"""
    try:
        aircraft_list = find_aircraft_by_icao24(icao24)
        
        return jsonify({
            'success': True,
            'aircraft': [{
                'id': a.id,
                'icao24': a.icao24,
                'callsign': a.callsign,
                'aircraft_type': a.aircraft_type,
                'origin_country': a.origin_country,
                'last_updated': a.last_updated.isoformat() if a.last_updated else None
            } for a in aircraft_list]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/aircraft/search/country/<country>', methods=['GET'])
def search_by_country(country):
    """API endpoint to search aircraft by origin country"""
    try:
        aircraft_list = find_aircraft_by_country(country)
        
        return jsonify({
            'success': True,
            'aircraft': [{
                'id': a.id,
                'icao24': a.icao24,
                'callsign': a.callsign,
                'aircraft_type': a.aircraft_type,
                'origin_country': a.origin_country,
                'last_updated': a.last_updated.isoformat() if a.last_updated else None
            } for a in aircraft_list]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def run_api_server(host='0.0.0.0', port=5001, debug=False):
    """Run the API server"""
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_api_server(debug=True)