# src/validate/raw_checks.py
import logging
from typing import Any
from src import config

logger = logging.getLogger(__name__)

class RawValidationError(Exception):
    """
    Raised when a raw data quality check fails.
    Signals the pipeline to halt before loading corrupt data.
    """
    pass

def check_weather_response(data: dict[str, Any], city: str) -> None:
    """
    Validate a raw weather API response before loading.
    Raises RawValidationError on any failed check.

    Checks:
        - 'hourly' key is present in the response
        - All expected variables exist inside 'hourly'
        - 'time' array is non-empty
        - Temperature values fall within a plausible range (-90 to 60 degrees C)

    Args:
        data: Raw response dict from WeatherExtractor.fetch()
        city: City name - used in error messaged for clarity

    Raises:
        RawValidationError: if any check fails
    """
    if "hourly" not in data.keys():
        raise RawValidationError(f"[{city}]: The 'hourly' key is not present in the response")
    
    hourly = data["hourly"]
    if not all(key in hourly.keys() for key in config.WEATHER_VARIABLES):
        raise RawValidationError(f"[{city}]: All expected variables do not exist inside 'hourly'")
    
    if not hourly["time"]:
        raise RawValidationError(f"[{city}]: The 'time' array is empty")
    
    low_temp = -90
    high_temp = 60

    temperature_fields = ["temperature_2m", "apparent_temperature", "temperature_80m", "temperature_120m"]
    for temp_field in temperature_fields:
        for temp in hourly[temp_field]:
            if temp is None:
                continue
            if not low_temp <= temp <= high_temp:
                raise RawValidationError(f"[{city}] {temp_field} value {temp} is outside plausible range")
    
    # Need to look into possible ranges and values for: humidity, dew point, precipitation, cloud cover, wind speed, and visibility


def check_air_quality_response(data: dict[str, Any], city: str) -> None:
    """
    Validate a raw air quality API response before loading.
    Raises RawValidationError on any failed check.

    Checks:
        - 'results' key is present in the response
        - 'results' list is non-empty
        - Each record contains required fields:
            location_id, timestamp, parameter, value, unit
        - 'parameter' values are within the expected set from config.AQ_PARAMETERS
        - 'value' is non-negative (pollution readings cannot be negative)

    Args: 
        data: Raw response dict from the AirQualityExtractor.fetch()
        city: City name - used in error messages for clarity

    Raises:
        RawValidationError: if any check fails
    """
    if "results" not in data.keys():
        raise RawValidationError(f"[{city}]: The 'results' key is not present in the response")
    
    results = data["results"]
    if not results:
        raise RawValidationError(f"[{city}]: The 'results' list is empty")
    
    for record in results:
        if not all(key in record.keys() for key in ["location_id", "timestamp", "parameter", "value", "unit"]):
            raise RawValidationError(f"[{city}]: Each record does not contain all required fields")
        
        if record["parameter"] not in config.AQ_PARAMETERS:
            raise RawValidationError(f"[{city}]: all 'parameter' values are not in the expected set")
        
        if record["value"] < 0:
            raise RawValidationError(f"[{city}]: There is a negative value when it shouldn't be there")
        
    
    
def run_raw_checks(weather_data: list[dict], aq_data: list[dict]) -> None:
    """
    Run all raw checks across all cities.
    Called after extraction, before loading.

    Iterates through all weather and air quality responses
    and calls the relevant check function for each.

    Args:
        weather_data: List of dicts from WeatherExtractor.fetch_all()
        aq_data:      List of dicts from AirQualityExtractor.fetch_all()

    Raises:
        RawValidationError: If any check fails for any city
    """
    weather_by_city = {d["city"]: d for d in weather_data}
    aq_by_city = {d["city"]: d for d in aq_data}

    for city in config.CITIES:
        check_weather_response(weather_by_city[city], city)
        check_air_quality_response(aq_by_city[city], city)
