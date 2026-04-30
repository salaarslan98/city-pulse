# src/load/loader.py
import logging
from typing import Any
from datetime import datetime

import duckdb
from src.load.db import get_connection, initialise_database
from src import config

logger = logging.getLogger(__name__)

def load_cities(conn: duckdb.DuckDBPyConnection, cities: dict[str, dict]) -> None:
    """
    Load cities from config into raw.cities.
    Uses INSERT OR IGNORE to prevent duplicates based on (city_name, lat, lon).

    Args:
        conn: An open DuckDB connection
        cities: Dictionary of city data - structure is config.CITIES
    """
    
    rows = [
        (idx + 1, city, data["lat"], data["lon"])
        for idx, (city, data) in enumerate(cities.items())
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO raw.cities (city_id, city_name, lat, lon)
        VALUES (?, ?, ?, ?)
        """, rows)

def load_weather_observations(
    conn: duckdb.DuckDBPyConnection,
    city_id: int,
    weather_data: dict[str, Any]
) -> None:
    """
    Load weather observations from an Open-Meteo API respnse

    Open-Meteo returns data in columnar format:
        "hourly": {
        "time": ["2026-04-20T00:00", ...],
        "temperature_2m": [15.2, ...],
        "precipitation": [0, ...],
        ...
    }

    This method pivots that into row format and loads into raw.weather_observations.
    Uses INSERT OR IGNORE to prevent duplicates based on (city_id, timestamp).

    Args:
        conn:           An open DuckDB connection
        city_id:        The city_id (from raw.cities) this data belongs to
        weather_data:   Raw API response dict from WeatherExtractor.fetch()
    """
    hourly = weather_data["hourly"]
    rows = [
        (city_id, timestamp, temperature_2m, apparent_temperature, relative_humidity_2m, dew_point_2m, precipitation, cloud_cover, wind_speed_10m, wind_speed_80m, temperature_80m, temperature_120m, visibility, datetime.now())
        for timestamp, temperature_2m, apparent_temperature, relative_humidity_2m, dew_point_2m, precipitation, cloud_cover, wind_speed_10m, wind_speed_80m, temperature_80m, temperature_120m, visibility in zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["apparent_temperature"],
            hourly["relative_humidity_2m"],
            hourly["dew_point_2m"],
            hourly["precipitation"],
            hourly["cloud_cover"],
            hourly["wind_speed_10m"],
            hourly["wind_speed_80m"],
            hourly["temperature_80m"],
            hourly["temperature_120m"],
            hourly["visibility"]
        )
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO raw.weather_observations (
            city_id, timestamp, temperature_2m, apparent_temperature,
            relative_humidity_2m, dew_point_2m, precipitation, cloud_cover,
            wind_speed_10m, wind_speed_80m, temperature_80m, temperature_120m,
            visibility, extracted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows
    )

    logger.info(f"Loaded {len(rows)} weather observations for city_id {city_id}")

def load_air_quality_measurements(
    conn: duckdb.DuckDBPyConnection,
    city_id: int,
    aq_data: dict[str, Any]
) -> None:
    """
    Load air quality measurements from an OpenAQ API response.
    
    OpenAQ returns data as a list of measurement records:
        "results": [
            {
                "location_id": 1234,
                "location_name": "Milano - Via Senato",
                "timestamp": "2026-04-20T10:00:00Z",
                "parameter": "pm25",
                "value": 35.2,
                "unit": "µg/m³"
            },
            ...
        ]
    
    This method loads those records into raw.air_quality_measurements.
    Uses INSERT OR IGNORE to prevent duplicates based on (location_id, timestamp, parameter).

    Args:
        conn:    An open DuckDB connection
        city_id: The city_id (from raw.cities) this data belongs to
        aq_data: Raw API response dict from AirQualityExtractor.fetch()
    """
    results = aq_data["results"]

    rows = [
        (city_id, record["location_id"], record["location_name"], record["timestamp"], record["parameter"], record["value"], record["unit"], datetime.now())
        for record in results
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO raw.air_quality_measurements (
        city_id, location_id, location_name, timestamp,
        parameter, value, unit, extracted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows     
    )
    logger.info(f"Loaded {len(rows)} air quality measurements for city_id {city_id}")
 
def run_full_load(weather_data: list[dict], aq_data: list[dict]) -> None:
    """
    End-to-end load orchestration.
    
    Initialises the database, loads all cities once,
    then loads all weather and air quality data.

    Args:
        weather_data: List of dicts from WeatherExtractor.fetch_all()
        aq_data:      List of dicts from AirQualityExtractor.fetch_all()
    """
    conn = get_connection()
    initialise_database(conn)
    load_cities(conn, config.CITIES)

    weather_by_city = {d["city"]: d for d in weather_data}
    aq_by_city = {d["city"]: d for d in aq_data}

    for city in config.CITIES:
        city_id = conn.execute("SELECT city_id FROM raw.cities WHERE city_name = ?", (city,)).fetchone()[0]
        load_weather_observations(conn, city_id, weather_by_city[city])
        load_air_quality_measurements(conn, city_id, aq_by_city[city])

    conn.close()
    logger.info("Full load complete")
    