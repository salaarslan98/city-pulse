#src/load/db.py
import duckdb
import logging
from pathlib import Path
from src import config

logger = logging.getLogger(__name__)

def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Open and return a connection to DuckDB database file.
    The path is read from config.DB_PATH

    Returns:
        An open DuckDB connection
    """
    connection = duckdb.connect(str(config.DB_PATH))
    return connection

def initialise_database(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Create the raw schema and all raw tables if they don't already exist.
    Safe to call on every pipeline run - existing tables are not modified.

    Creates:
        - raw schema
        - raw.cities
        - raw.weather_observations
        - raw.air_quality_measurements
    
    Args:
        conn: An open DuckDB connection
    """

    conn.execute("CREATE SCHEMA IF NOT EXISTS raw")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw.cities (
            city_id         INTEGER PRIMARY KEY,
            city_name       VARCHAR,
            lat             DOUBLE,
            lon             DOUBLE,
            UNIQUE (city_name, lat, lon)
            )
        """)

    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw.weather_observations (
            city_id           INTEGER,
            timestamp         TIMESTAMP,
            temperature_2m    DOUBLE,
            apparent_temperature DOUBLE,
            relative_humidity_2m DOUBLE,
            dew_point_2m      DOUBLE,
            precipitation     DOUBLE,
            cloud_cover       DOUBLE,
            wind_speed_10m    DOUBLE,
            wind_speed_80m    DOUBLE,
            temperature_80m   DOUBLE,
            temperature_120m  DOUBLE,
            visibility        DOUBLE,
            extracted_at      TIMESTAMP,
            UNIQUE (city_id, timestamp)
            )
        """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw.air_quality_measurements (
            city_id           INTEGER,
            location_id       INTEGER,
            location_name     VARCHAR,
            timestamp         TIMESTAMP,
            parameter         VARCHAR,
            value             DOUBLE,
            unit              VARCHAR,
            extracted_at      TIMESTAMP,
            UNIQUE (location_id, timestamp, parameter)
            )
        """)

    logger.info("Database initialised")