"""
Database utility functions for the Aircraft Search Prediction System
"""

from datetime import datetime
import json
from database_models import (
    get_session, Aircraft, AircraftPosition, 
    SearchQuery, SearchResult, EmergencyPrediction
)

def create_or_update_aircraft(icao24, callsign=None, aircraft_type=None, origin_country=None):
    """
    Create a new aircraft record or update an existing one
    
    Parameters:
    -----------
    icao24 : str
        The ICAO24 address of the aircraft
    callsign : str, optional
        The callsign of the aircraft
    aircraft_type : str, optional
        The type of aircraft
    origin_country : str, optional
        The country of origin
        
    Returns:
    --------
    dict
        A dictionary containing the created or updated aircraft record's data
    """
    session = get_session()
    try:
        # Check if aircraft already exists
        aircraft = session.query(Aircraft).filter_by(icao24=icao24).first()
        
        if aircraft:
            # Update existing aircraft
            if callsign:
                aircraft.callsign = callsign
            if aircraft_type:
                aircraft.aircraft_type = aircraft_type
            if origin_country:
                aircraft.origin_country = origin_country
            aircraft.last_updated = datetime.utcnow()
        else:
            # Create new aircraft
            aircraft = Aircraft(
                icao24=icao24,
                callsign=callsign,
                aircraft_type=aircraft_type,
                origin_country=origin_country
            )
            session.add(aircraft)
            
        session.commit()
        
        # Create a dictionary of the aircraft data before closing the session
        aircraft_data = {
            'id': aircraft.id,
            'icao24': aircraft.icao24,
            'callsign': aircraft.callsign,
            'aircraft_type': aircraft.aircraft_type,
            'origin_country': aircraft.origin_country,
            'last_updated': aircraft.last_updated.isoformat() if aircraft.last_updated else None
        }
        
        return aircraft_data
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def store_aircraft_position(
    aircraft_id, latitude, longitude, altitude=None, 
    ground_speed=None, heading=None, vertical_speed=None, on_ground=False
):
    """
    Store a position record for an aircraft
    
    Parameters:
    -----------
    aircraft_id : int
        The ID of the aircraft in the database
    latitude : float
        The latitude of the aircraft
    longitude : float
        The longitude of the aircraft
    altitude : float, optional
        The altitude of the aircraft in feet
    ground_speed : float, optional
        The ground speed of the aircraft in knots
    heading : float, optional
        The heading of the aircraft in degrees
    vertical_speed : float, optional
        The vertical speed of the aircraft in feet per minute
    on_ground : bool, optional
        Whether the aircraft is on the ground
        
    Returns:
    --------
    AircraftPosition
        The created position record
    """
    session = get_session()
    try:
        position = AircraftPosition(
            aircraft_id=aircraft_id,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            ground_speed=ground_speed,
            heading=heading,
            vertical_speed=vertical_speed,
            on_ground=on_ground
        )
        session.add(position)
        session.commit()
        return position
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def store_search_query(search_type, search_value):
    """
    Store a search query
    
    Parameters:
    -----------
    search_type : str
        The type of search (callsign, icao24, country)
    search_value : str
        The value being searched for
        
    Returns:
    --------
    SearchQuery
        The created search query record
    """
    session = get_session()
    try:
        query = SearchQuery(
            search_type=search_type,
            search_value=search_value
        )
        session.add(query)
        session.commit()
        return query
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def store_search_result(query_id, aircraft_id):
    """
    Store a search result
    
    Parameters:
    -----------
    query_id : int
        The ID of the search query
    aircraft_id : int
        The ID of the aircraft found
        
    Returns:
    --------
    SearchResult
        The created search result record
    """
    session = get_session()
    try:
        result = SearchResult(
            query_id=query_id,
            aircraft_id=aircraft_id
        )
        session.add(result)
        session.commit()
        return result
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def store_emergency_prediction(
    aircraft_id, current_position, aircraft_params, wind_conditions, 
    aircraft_type, glide_ratio, prediction_results
):
    """
    Store an emergency landing prediction
    
    Parameters:
    -----------
    aircraft_id : int
        The ID of the aircraft
    current_position : dict
        The current position of the aircraft
    aircraft_params : dict
        The flight parameters of the aircraft
    wind_conditions : dict
        The wind conditions
    aircraft_type : str
        The type of aircraft
    glide_ratio : float
        The glide ratio used for the prediction
    prediction_results : dict
        The results of the prediction
        
    Returns:
    --------
    EmergencyPrediction
        The created prediction record
    """
    session = get_session()
    try:
        prediction = EmergencyPrediction(
            aircraft_id=aircraft_id,
            
            # Current position and parameters
            latitude=current_position['latitude'],
            longitude=current_position['longitude'],
            altitude=current_position['altitude'],
            ground_speed=aircraft_params.get('ground_speed'),
            heading=aircraft_params.get('heading'),
            vertical_speed=aircraft_params.get('vertical_speed'),
            
            # Wind conditions
            wind_speed=wind_conditions.get('speed'),
            wind_direction=wind_conditions.get('direction'),
            
            # Aircraft type and glide ratio
            aircraft_type=aircraft_type,
            glide_ratio=glide_ratio,
            
            # Prediction results
            predicted_landing_latitude=prediction_results['landingPosition'][0],
            predicted_landing_longitude=prediction_results['landingPosition'][1],
            glide_distance=prediction_results.get('glideDistance'),
            glide_time=prediction_results.get('glideTime'),
            uncertainty_radius=prediction_results.get('uncertaintyRadius'),
            
            # Additional details
            details=prediction_results.get('details', {})
        )
        session.add(prediction)
        session.commit()
        return prediction
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_recent_aircraft(limit=100):
    """
    Get recently updated aircraft
    
    Parameters:
    -----------
    limit : int, optional
        The maximum number of aircraft to return
        
    Returns:
    --------
    list
        A list of aircraft objects
    """
    session = get_session()
    try:
        aircraft = session.query(Aircraft).order_by(
            Aircraft.last_updated.desc()
        ).limit(limit).all()
        return aircraft
    finally:
        session.close()

def get_aircraft_positions(aircraft_id, limit=10):
    """
    Get recent positions for an aircraft
    
    Parameters:
    -----------
    aircraft_id : int
        The ID of the aircraft
    limit : int, optional
        The maximum number of positions to return
        
    Returns:
    --------
    list
        A list of position objects
    """
    session = get_session()
    try:
        positions = session.query(AircraftPosition).filter_by(
            aircraft_id=aircraft_id
        ).order_by(
            AircraftPosition.timestamp.desc()
        ).limit(limit).all()
        return positions
    finally:
        session.close()

def get_search_history(limit=10):
    """
    Get recent search queries
    
    Parameters:
    -----------
    limit : int, optional
        The maximum number of queries to return
        
    Returns:
    --------
    list
        A list of search query objects
    """
    session = get_session()
    try:
        queries = session.query(SearchQuery).order_by(
            SearchQuery.timestamp.desc()
        ).limit(limit).all()
        return queries
    finally:
        session.close()

def get_prediction_history(limit=10):
    """
    Get recent emergency predictions
    
    Parameters:
    -----------
    limit : int, optional
        The maximum number of predictions to return
        
    Returns:
    --------
    list
        A list of prediction objects
    """
    session = get_session()
    try:
        predictions = session.query(EmergencyPrediction).order_by(
            EmergencyPrediction.timestamp.desc()
        ).limit(limit).all()
        return predictions
    finally:
        session.close()

def find_aircraft_by_callsign(callsign):
    """
    Find aircraft by callsign
    
    Parameters:
    -----------
    callsign : str
        The callsign to search for
        
    Returns:
    --------
    list
        A list of matching aircraft
    """
    session = get_session()
    try:
        aircraft = session.query(Aircraft).filter(
            Aircraft.callsign.ilike(f"%{callsign}%")
        ).all()
        return aircraft
    finally:
        session.close()

def find_aircraft_by_icao24(icao24):
    """
    Find aircraft by ICAO24 address
    
    Parameters:
    -----------
    icao24 : str
        The ICAO24 address to search for
        
    Returns:
    --------
    list
        A list of matching aircraft
    """
    session = get_session()
    try:
        aircraft = session.query(Aircraft).filter(
            Aircraft.icao24.ilike(f"%{icao24}%")
        ).all()
        return aircraft
    finally:
        session.close()

def find_aircraft_by_country(country):
    """
    Find aircraft by origin country
    
    Parameters:
    -----------
    country : str
        The origin country to search for
        
    Returns:
    --------
    list
        A list of matching aircraft
    """
    session = get_session()
    try:
        aircraft = session.query(Aircraft).filter(
            Aircraft.origin_country.ilike(f"%{country}%")
        ).all()
        return aircraft
    finally:
        session.close()

def get_aircraft_by_id(aircraft_id):
    """
    Get an aircraft by ID
    
    Parameters:
    -----------
    aircraft_id : int
        The ID of the aircraft
        
    Returns:
    --------
    Aircraft
        The aircraft object or None if not found
    """
    session = get_session()
    try:
        aircraft = session.query(Aircraft).filter_by(id=aircraft_id).first()
        return aircraft
    finally:
        session.close()