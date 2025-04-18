"""
Database models for the Aircraft Search Prediction System
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Get database URL from environment variables
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Create SQLAlchemy engine with a fallback for development
if not DATABASE_URL:
    # Use a SQLite database as fallback for testing/development
    DATABASE_URL = 'sqlite:///aircraft_tracker.db'
    print("Warning: No DATABASE_URL environment variable found. Using SQLite database.")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

class Aircraft(Base):
    """
    Aircraft model to store information about tracked aircraft
    """
    __tablename__ = 'aircraft'
    
    id = Column(Integer, primary_key=True)
    icao24 = Column(String(24), nullable=False, unique=True, index=True)
    callsign = Column(String(10))
    aircraft_type = Column(String(50))
    origin_country = Column(String(100))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    positions = relationship("AircraftPosition", back_populates="aircraft", cascade="all, delete-orphan")
    search_results = relationship("SearchResult", back_populates="aircraft")
    
    def __repr__(self):
        return f"<Aircraft(icao24='{self.icao24}', callsign='{self.callsign}')>"

class AircraftPosition(Base):
    """
    AircraftPosition model to store position and flight data for aircraft
    """
    __tablename__ = 'aircraft_positions'
    
    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey('aircraft.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Position data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)  # in feet
    ground_speed = Column(Float)  # in knots
    heading = Column(Float)  # in degrees
    vertical_speed = Column(Float)  # in feet per minute
    on_ground = Column(Boolean, default=False)
    
    # Relationship
    aircraft = relationship("Aircraft", back_populates="positions")
    
    def __repr__(self):
        return f"<AircraftPosition(icao24='{self.aircraft.icao24}', time='{self.timestamp}')>"

class SearchQuery(Base):
    """
    SearchQuery model to store user search parameters
    """
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True)
    search_type = Column(String(50), nullable=False)  # callsign, icao24, country
    search_value = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    results = relationship("SearchResult", back_populates="query", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SearchQuery(type='{self.search_type}', value='{self.search_value}')>"

class SearchResult(Base):
    """
    SearchResult model to store search results
    """
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey('search_queries.id'), nullable=False)
    aircraft_id = Column(Integer, ForeignKey('aircraft.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    query = relationship("SearchQuery", back_populates="results")
    aircraft = relationship("Aircraft", back_populates="search_results")
    
    def __repr__(self):
        return f"<SearchResult(aircraft='{self.aircraft.icao24}')>"

class EmergencyPrediction(Base):
    """
    EmergencyPrediction model to store emergency landing predictions
    """
    __tablename__ = 'emergency_predictions'
    
    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey('aircraft.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Aircraft parameters at prediction time
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    ground_speed = Column(Float)
    heading = Column(Float)
    vertical_speed = Column(Float)
    
    # Environment conditions
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    
    # Prediction parameters
    aircraft_type = Column(String(50))
    glide_ratio = Column(Float)
    
    # Prediction results
    predicted_landing_latitude = Column(Float, nullable=False)
    predicted_landing_longitude = Column(Float, nullable=False)
    glide_distance = Column(Float)  # in nautical miles
    glide_time = Column(Float)  # in minutes
    uncertainty_radius = Column(Float)  # in km
    
    # Additional details if needed
    details = Column(JSON)
    
    # Relationships
    aircraft = relationship("Aircraft")
    
    def __repr__(self):
        return f"<EmergencyPrediction(aircraft='{self.aircraft.icao24}', time='{self.timestamp}')>"

def create_tables():
    """Create all the tables in the database"""
    Base.metadata.create_all(engine)

def get_session():
    """Get a session to interact with the database"""
    Session = sessionmaker(bind=engine)
    return Session()

# Create tables if this file is run directly
if __name__ == '__main__':
    create_tables()
    print("Database tables created successfully.")